import base64
import datetime
import ftplib
import json
import os
import tempfile
from collections import defaultdict
from collections.abc import Iterable
from io import BytesIO
from urllib.parse import urlparse
import time

from django.db import transaction
from hl7apy import VALIDATION_LEVEL, core
from hl7apy.parser import parse_message, parse_field

from clients.models import Individual, CardBase
from contracts.models import PriceName
from directions.models import Napravleniya, RegisteredOrders, NumberGenerator, TubesRegistration, IstochnikiFinansirovaniya, NapravleniyaHL7LinkFiles
from ftp_orders.sql_func import get_tubesregistration_id_by_iss
from hospitals.models import Hospitals
from directory.models import Researches
from laboratory.settings import BASE_DIR
from laboratory.utils import current_time
from slog.models import Log
from users.models import DoctorProfile


class ServiceNotFoundException(Exception):
    pass


class InvalidOrderNumberException(Exception):
    pass


class FailedCreatingDirectionsException(Exception):
    pass


class NoValidNumberGeneratorException(Exception):
    pass


class FTPConnection:
    def __init__(self, url, hospital: Hospitals):
        parsed_url = urlparse(url)
        self.hospital = hospital
        self.url = url
        self.hostname = parsed_url.hostname
        self.username = parsed_url.username
        self.password = parsed_url.password
        self.directory = parsed_url.path

        self.ftp = None
        self.connected = False
        self.encoding = 'utf-8'

    @property
    def name(self):
        return self.hospital.safe_short_title

    def log(self, *msg, color=None, level='INFO '):
        message = ""
        if color:
            message = f"\033[{color}m{message}"

        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        message += f"[{level}] {current_time}: {self.name} {self.url} {' '.join([str(x) for x in (msg if isinstance(msg, Iterable) else [msg])])}"

        if color:
            message += "\033[0m"

        print(message)  # noqa: F201

    def error(self, *msg):
        self.log(*msg, color='91', level='ERROR')

    def connect(self, forced=False, encoding='utf-8'):
        if forced:
            self.disconnect()
        if not self.connected:
            self.ftp = ftplib.FTP(self.hostname, encoding=encoding)
            self.ftp.login(self.username, self.password)
            self.ftp.cwd(self.directory)
            self.connected = True
            self.encoding = encoding
            self.log("Connected with encoding", self.encoding)

    def disconnect(self):
        if self.connected:
            try:
                self.ftp.quit()
            except ftplib.all_errors:
                pass
            finally:
                self.ftp = None
                self.connected = False

    def get_file_list(self, is_retry=False):
        try:
            file_list = self.ftp.nlst()
        except ftplib.error_perm as resp:
            if str(resp).startswith('550'):
                file_list = []
            else:
                raise resp
        except UnicodeDecodeError as e:
            self.error(f"UnicodeDecodeError: {e}")
            if not is_retry:
                self.log("Retrying connection with encoding cp1251")
                self.connect(forced=True, encoding='cp1251')
                return self.get_file_list(is_retry=True)
            else:
                raise e
        return file_list

    def delete_file(self, file):
        try:
            self.ftp.delete(file)
            self.log(f"Deleted file {file}")
        except Exception as e:
            self.error(f"Error deleting file {file}: {e}")

    def read_file_as_text(self, file):
        self.log(f"Reading file {file}")
        with tempfile.NamedTemporaryFile() as f:
            self.connect()
            self.ftp.retrbinary(f"RETR {file}", f.write)
            f.seek(0)
            content = f.read()
            try:
                return content.decode('utf-8-sig')
            except UnicodeDecodeError as e:
                self.error(f"UnicodeDecodeError: {e}")
                self.log('Trying again with encoding cp1251')
                return content.decode('cp1251')

    def write_file_as_text(self, file, content):
        self.log(f"Writing file {file}")
        self.connect()
        self.ftp.storbinary(f"STOR {file}", BytesIO(content.encode('utf-8')))
        self.log(f"Wrote file {file}")

    def read_file_as_hl7(self, file):
        content = self.read_file_as_text(file).strip('\x0b').strip('\x0c')
        self.log(f"{file}\n{content}")
        content = content.replace("\n", "\r")
        try:
            hl7_result = parse_message(content, validation_level=VALIDATION_LEVEL.QUIET)

            return hl7_result, content
        except Exception as e:
            self.error(f"Error parsing file {file}: {e}")
            return None, None

    def pull_order(self, file: str):
        if not file.endswith('.ord'):
            self.error(f"Skipping file {file} because it does not end with '.ord'")
            return
        if RegisteredOrders.objects.filter(file_name=file).exists():
            self.error(f"Skipping file {file} because it already exists")
            return

        hl7_result, hl7_content = self.read_file_as_hl7(file)

        if not hl7_content or not hl7_result:
            self.error(f"Skipping file {file} because it could not be parsed")
            return

        self.log(f"HL7 parsed")
        patient = hl7_result.ORM_O01_PATIENT[0]
        pid = patient.PID[0]

        pv1 = hl7_result.ORM_O01_PATIENT.ORM_O01_PATIENT_VISIT.PV1.PV1_20.value.split("^")
        if len(pv1) > 1:
            price_symbol_code = pv1[-1]
        else:
            price_symbol_code = pv1[0]
        base = CardBase.objects.filter(internal_type=True).first()
        if pv1[0].lower() in ["наличные", "платно", "средства граждан"]:
            finsource = IstochnikiFinansirovaniya.objects.filter(base=base, title="Платно", hide=False).first()
        else:
            finsource = IstochnikiFinansirovaniya.objects.filter(base=base, title__in=["Договор"], hide=False).first()

        price_name = PriceName.objects.filter(symbol_code=price_symbol_code).first()

        orders = hl7_result.ORM_O01_ORDER[0].children[0]
        patient_id_company = pid.PID_2.value
        print("patient_id_company", patient_id_company)

        fio = pid.PID_5
        family = fio.PID_5_1.value
        name = fio.PID_5_2.value
        patronymic = fio.PID_5_3.value if hasattr(fio, 'PID_5_3') else ''

        birthday = pid.PID_7.value
        if len(birthday) == 8:
            birthday = f"{birthday[:4]}-{birthday[4:6]}-{birthday[6:]}"

        sex = {'m': 'м', 'f': 'ж'}.get(pid.PID_8.value.lower(), 'ж')

        snils = pid.PID_19.value
        snils = snils.replace("-", "").replace(" ", "")

        adds_data = pid.to_er7().split("|")[13].split("~")

        tel_home = adds_data[0] if adds_data[0] else ""
        tel_additional = adds_data[1] if adds_data[1] else ""
        tel_work = adds_data[2] if adds_data[2] else ""
        email = adds_data[3] if adds_data[3] else ""

        print("tel_home", tel_home)
        print("tel_additional", tel_additional)
        print("tel_work", tel_work)
        print("email", email)
        email_data = base64.b64encode(email).decode("latin1")

        orders_by_numbers = defaultdict(list)
        additional_order_number_by_service = defaultdict(list)

        for order in orders.children:
            obr = order.children[0]
            orders_by_numbers[obr.OBR_3.value].append(obr.OBR_4.OBR_4_4.value)
            additional_order_number_by_service[obr.OBR_4.OBR_4_4.value] = obr.OBR_2.OBR_2_1.value

        orders_by_numbers = dict(orders_by_numbers)

        self.log(family, name, patronymic, birthday, sex)
        self.log(orders_by_numbers)

        try:
            card = Individual.import_from_simple_data(
                {
                    "family": family,
                    "name": name,
                    "patronymic": patronymic,
                    "sex": sex,
                    "birthday": birthday,
                    "snils": snils
                },
                self.hospital,
                patient_id_company

            )
            self.log("Card", card)

            directions = {}
            order_numbers = []

            with transaction.atomic():
                doc = DoctorProfile.get_system_profile()
                services_by_order_number = {}
                services_by_additional_order_num = {}
                for order_number, services_codes in orders_by_numbers.items():
                    for service_code in services_codes:
                        service = Researches.objects.filter(hide=False, internal_code=service_code).first()
                        if not service:
                            raise ServiceNotFoundException(f"Service {service_code} not found")
                        if order_number not in services_by_order_number:
                            services_by_order_number[order_number] = []
                        services_by_order_number[order_number].append(service.pk)
                        services_by_additional_order_num[service.pk] = additional_order_number_by_service.get(service_code, "")

                for order_number_str, services in services_by_order_number.items():
                    order_numbers.append(order_number_str)

                    if not order_number_str.isdigit():
                        raise InvalidOrderNumberException(f'Number {order_number} is not digit')
                    order_number = int(order_number_str)
                    if order_number <= 0:
                        raise InvalidOrderNumberException(f'Number {order_number} need to be greater than 0')
                    if not NumberGenerator.check_value_for_organization(self.hospital, order_number):
                        raise InvalidOrderNumberException(f'Number {order_number} not valid. May be NumberGenerator is over or order number exists')

                    external_order = RegisteredOrders.objects.create(
                        order_number=order_number,
                        organization=self.hospital,
                        services=orders_by_numbers[order_number_str],
                        patient_card=card,
                        file_name=file,
                    )
                    result = Napravleniya.gen_napravleniya_by_issledovaniya(
                        card.pk,
                        "",
                        finsource.pk,
                        "",
                        None,
                        doc,
                        {-1: services},
                        {},
                        False,
                        {},
                        vich_code="",
                        count=1,
                        discount=0,
                        rmis_slot=None,
                        external_order=external_order,
                        hospital_override=self.hospital.pk,
                        services_by_additional_order_num=services_by_additional_order_num,
                        price_name=price_name.pk,
                    )

                    if not result['r']:
                        raise FailedCreatingDirectionsException(result.get('message') or "Failed creating directions")

                    self.log("Created local directions:", result['list_id'])
                    for direction in result['list_id']:
                        directions[direction] = orders_by_numbers[order_number_str]

                    for direction in Napravleniya.objects.filter(pk__in=result['list_id'], need_order_redirection=True):
                        self.log("Direction", direction.pk, "marked as redirection to", direction.external_executor_hospital)
                        with tempfile.NamedTemporaryFile() as f:
                            self.connect()
                            self.ftp.retrbinary(f"RETR {file}", f.write)
                            f.seek(0)
                            path_file = NapravleniyaHL7LinkFiles.create_hl7_file_path(direction.pk, file)
                            with open(path_file, 'wb') as fnew:
                                fnew.write(f.read())
                        NapravleniyaHL7LinkFiles.objects.create(napravleniye_id=direction.pk, upload_file=path_file, file_type="HL7_ORIG_ORDER", )

            self.delete_file(file)

            Log.log(
                json.dumps(order_numbers),
                190000,
                None,
                {
                    "org": self.hospital.safe_short_title,
                    "content": hl7_content,
                    "directions": directions,
                    "card": card.number_with_type(),
                },
            )
        except Exception as e:
            self.error(f"Exception: {e}")


    def pull_result(self, file: str):
        if not file.endswith('.res'):
            self.error(f"Skipping file {file} because it does not end with '.res'")
            return

        hl7_result, hl7_content = self.read_file_as_hl7(file)

        if not hl7_content or not hl7_result:
            self.error(f"Skipping file {file} because it could not be parsed")
            return

        self.log(f"HL7 parsed")


    def push_order(self, direction: Napravleniya):
        hl7 = core.Message("ORM_O01", validation_level=VALIDATION_LEVEL.QUIET)

        hl7.msh.msh_3 = "L2"
        hl7.msh.msh_4 = "ORDER"
        hl7.msh.msh_5 = "qLIS"
        hl7.msh.msh_6 = "LukaLab"
        hl7.msh.msh_9 = "ORM^O01"
        hl7.msh.msh_10 = "1"
        hl7.msh.msh_11 = "P"

        individual = direction.client.individual
        data_indivdual = direction.client.get_data_individual()
        patient = hl7.add_group("ORM_O01_PATIENT")
        patient.pid.pid_2 = str(direction.client.pk)
        patient.pid.pid_5 = f"{individual.family}^{individual.name}^{individual.patronymic}"
        patient.pid.pid_7 = individual.birthday.strftime("%Y%m%d")
        patient.pid.pid_8 = individual.sex.upper()
        byte_email = direction.client.email.encode('utf-8')
        field_13 = f"{direction.client.phone.replace(' ', '').replace('-', '')}~~~{base64.b64encode(byte_email).decode('UTF-8')}"
        print(field_13)
        patient.pid.pid_13.value = field_13
        patient.pid.pid_19 = data_indivdual['snils']

        pv = hl7.add_group("ORM_O01_PATIENT_VISIT")
        pv.PV1.PV1_2.value = "O"
        pv.PV1.PV1_20.value = "Наличные"
        pv.PV1.PV1_44.value = direction.data_sozdaniya.strftime("%Y%m%d")
        pv.PV1.PV1_46.value = ""

        created_at = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        hl7.ORM_O01_ORDER.orc.orc_1 = "1"

        ordd = hl7.ORM_O01_ORDER.add_group("ORM_O01_ORDER_DETAIL")

        with transaction.atomic():
            direction.need_order_redirection = False
            direction.time_send_hl7 = current_time()
            direction.save(update_fields=['time_send_hl7', 'need_order_redirection'])

            n = 0

            for iss in direction.issledovaniya_set.all():
                n += 1
                obr = ordd.add_segment("OBR")
                obr.obr_1 = str(n)
                obr.obr_2 = f"L2_{iss.pk}^{direction.hospital.hl7_sender_application}"
                tube_data = [i.tube_number for i in get_tubesregistration_id_by_iss(iss.pk)]
                obr.obr_3.value = str(tube_data[0])
                obr.obr_4.obr_4_4.value = iss.research.internal_code
                obr.obr_4.obr_4_5.value = iss.research.title.replace(" ", "_")
                obr.obr_7.value = created_at
                obr.obr_27.value = "^^^^^"
                obr.obr_34.value = ""

            content = hl7.value.replace("\r", "\n").replace("ORC|1\n", "")
            content = content.replace("R", "~").replace("\\", "")
            filename = f"form1c_orm_{direction.pk}_{created_at}.ord"
            print(content)

            self.log('Writing file', filename, '\n', content)
            self.write_file_as_text(filename, content)

            Log.log(
                direction.pk,
                190001,
                None,
                {
                    "org": self.hospital.safe_short_title,
                    "content": content,
                },
            )


    def push_tranfer_file_order(self, direction: Napravleniya, registered_orders_ids, directions_to_sync):
        created_at = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        directons_external_order_group = Napravleniya.objects.filter(external_order_id__in=registered_orders_ids)
        with transaction.atomic():
            for i in directons_external_order_group:
                i.need_order_redirection = False
                i.time_send_hl7 = current_time()
                i.save(update_fields=['time_send_hl7', 'need_order_redirection', 'need_order_redirection'])
            hl7_file = NapravleniyaHL7LinkFiles.objects.filter(napravleniye=direction).first()

            hl7_rule_file = os.path.join(BASE_DIR, 'ftp_orders', 'hl7_rule', direction.hospital.hl7_rule_file)
            if hl7_rule_file:
                with open(hl7_rule_file) as json_file:
                    data = json.load(json_file)
                    data = data['order']
                    need_replace_field = data['needReplaceField']
                mod_lines = []
                with open(f"{hl7_file.upload_file.name}", 'r') as fp:
                    for n, line in enumerate(fp, 1):
                        line = line.rstrip('\n')
                        line_new = line.split("|")
                        if line_new[0] in need_replace_field.keys():
                            field_replace = need_replace_field[line_new[0]]
                            for fr in field_replace:
                                if fr == "2":
                                    line_new[int(fr)] = direction.external_executor_hospital.hl7_sender_application
                                elif fr == "3":
                                    line_new[int(fr)] = direction.external_executor_hospital.short_title
                        mod_lines.append("|".join(line_new))
            path_file = NapravleniyaHL7LinkFiles.create_hl7_file_path(direction.pk, f"{hl7_file.upload_file.name}_mod")

            with open(path_file, "w") as file:
                for line in mod_lines:
                    file.write(line + '\n')
            file.close()
            with open(path_file, "r") as file:
                content = file.read()

            self.log('Writing file', path_file, '\n', content)
            filename = f"form1c_orm_{direction.pk}_{created_at}.ord"
            self.write_file_as_text(filename, content)

            for k in directons_external_order_group:
                directions_to_sync.remove(k)

            Log.log(
                direction.pk,
                190001,
                None,
                {
                    "org": self.hospital.safe_short_title,
                    "content": content,
                },
            )


MAX_LOOP_TIME = 600


def get_hospitals_pull_orders():
    hospitals = Hospitals.objects.filter(orders_pull_by_numbers__isnull=False, hide=False)
    return hospitals


def process_pull_orders():
    processed_files_by_url = defaultdict(set)

    hospitals = get_hospitals_pull_orders()

    print('Getting ftp links')  # noqa: F201
    ftp_links = {x.orders_pull_by_numbers: x for x in hospitals}

    ftp_connections = {}

    for ftp_url in ftp_links:
        ftp_connection = FTPConnection(ftp_url, hospital=ftp_links[ftp_url])
        ftp_connections[ftp_url] = ftp_connection

    time_start = time.time()

    while time.time() - time_start < MAX_LOOP_TIME:
        print(f'Iterating over {len(ftp_links)} servers')  # noqa: F201
        for ftp_url, ftp_connection in ftp_connections.items():
            processed_files_new = set()
            try:
                ftp_connection.connect()
                file_list = ftp_connection.get_file_list()

                for file in file_list:
                    processed_files_new.add(file)

                    if file not in processed_files_by_url[ftp_url]:
                        ftp_connection.pull_order(file)

            except ftplib.all_errors as e:
                processed_files_new.update(processed_files_by_url[ftp_url])
                ftp_connection.error(f"error: {e}")
                ftp_connection.log("Disconnecting...")
                ftp_connection.disconnect()

            processed_files_by_url[ftp_url] = processed_files_new

        time.sleep(5)

    for _, ftp_connection in ftp_connections.items():
        ftp_connection.disconnect()


def process_pull_start_orders():
    print('Starting pull_orders process')  # noqa: F201
    while True:
        process_pull_orders()
        time.sleep(1)


def get_hospitals_push_orders():
    hospitals = Hospitals.objects.filter(orders_push_by_numbers__isnull=False, is_external_performing_organization=True, hide=False)
    return hospitals


def process_push_orders():
    hospitals = get_hospitals_push_orders()

    print('Getting ftp links')  # noqa: F201
    ftp_links = {x.orders_push_by_numbers: x for x in hospitals}

    ftp_connections = {}

    for ftp_url in ftp_links:
        ftp_connection = FTPConnection(ftp_url, hospital=ftp_links[ftp_url])
        ftp_connections[ftp_url] = ftp_connection

    time_start = time.time()

    while time.time() - time_start < MAX_LOOP_TIME:
        print(f'Iterating over {len(ftp_links)} servers')  # noqa: F201
        for ftp_url, ftp_connection in ftp_connections.items():
            directions_to_sync = []
            for direction in Napravleniya.objects.filter(external_executor_hospital=ftp_connection.hospital, need_order_redirection=True)[:50]:
                is_recieve = False
                for tube in TubesRegistration.objects.filter(issledovaniya__napravleniye=direction).distinct():
                    is_recieve = True
                    if tube.time_recive is None:
                        is_recieve = False
                if is_recieve:
                    directions_to_sync.append(direction)

            ftp_connection.log(f"Directions to sync: {[d.pk for d in directions_to_sync]}")

            if directions_to_sync:
                try:
                    ftp_connection.connect()
                    for direction in directions_to_sync:
                        if direction.external_order and direction.need_order_redirection:
                            registered_orders_ids = direction.external_order.get_registered_orders_by_file_name()
                            ftp_connection.push_tranfer_file_order(direction, registered_orders_ids, directions_to_sync)
                        else:
                            ftp_connection.push_order(direction)

                except ftplib.all_errors as e:
                    ftp_connection.error(f"error: {e}")
                    ftp_connection.log("Disconnecting...")
                    ftp_connection.disconnect()

        time.sleep(5)

    for _, ftp_connection in ftp_connections.items():
        ftp_connection.disconnect()


def process_push_orders_start():
    print('Starting push_orders process')  # noqa: F201
    while True:
        process_push_orders()
        time.sleep(1)


def get_hospitals_pull_results():
    hospitals = Hospitals.objects.filter(result_pull_by_numbers__isnull=False, hide=False)
    return hospitals


def process_pull_results():
    processed_files_by_url = defaultdict(set)

    hospitals = get_hospitals_pull_results()
    print(hospitals)

    print('Getting ftp links')  # noqa: F201
    ftp_links = {x.result_pull_by_numbers: x for x in hospitals}

    ftp_connections = {}

    for ftp_url in ftp_links:
        ftp_connection = FTPConnection(ftp_url, hospital=ftp_links[ftp_url])
        ftp_connections[ftp_url] = ftp_connection

    time_start = time.time()

    while time.time() - time_start < MAX_LOOP_TIME:
        print(f'Iterating over {len(ftp_links)} servers')  # noqa: F201
        for ftp_url, ftp_connection in ftp_connections.items():
            processed_files_new = set()
            try:
                ftp_connection.connect()
                file_list = ftp_connection.get_file_list()

                for file in file_list:
                    processed_files_new.add(file)

                    if file not in processed_files_by_url[ftp_url]:
                        ftp_connection.pull_result(file)

            except ftplib.all_errors as e:
                processed_files_new.update(processed_files_by_url[ftp_url])
                ftp_connection.error(f"error: {e}")
                ftp_connection.log("Disconnecting...")
                ftp_connection.disconnect()

            processed_files_by_url[ftp_url] = processed_files_new

        time.sleep(5)

    for _, ftp_connection in ftp_connections.items():
        ftp_connection.disconnect()


def process_pull_start_results():
    print('Starting pull_orders process')  # noqa: F201
    while True:
        process_pull_results()
        time.sleep(1)
