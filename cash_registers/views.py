import uuid

import pytz

from cash_registers.models import CashRegister, Shift, Cheque, ChequeItems
import cash_registers.req as cash_req
import cash_registers.sql_func as sql_func
from clients.models import Card, CardBase
from contracts.sql_func import get_researches_and_coasts_in_price
from directions.models import IstochnikiFinansirovaniya
from laboratory.settings import TIME_ZONE
from laboratory.utils import current_time


def get_cash_registers():
    result = CashRegister.get_cash_registers()
    return result


def open_shift(cash_register_id: int, doctor_profile_id: int):
    result = {"ok": True, "message": ""}
    shift_job_data = Shift.get_shift_job_data(doctor_profile_id, cash_register_id)
    operator_data, cash_register_data, uuid_data = shift_job_data["operator_data"], shift_job_data["cash_register_data"], shift_job_data["uuid_data"]
    check_cash_register = cash_req.check_cash_register(cash_register_data)
    if check_cash_register["ok"]:
        job_result = cash_req.open_shift(uuid_data, cash_register_data, operator_data)
        if job_result["ok"]:
            Shift.open_shift(str(uuid_data), cash_register_id, doctor_profile_id)
        else:
            result = job_result
    else:
        result = check_cash_register
    return result


def close_shift(cash_register_id: int, doctor_profile_id: int):
    result = {"ok": True, "message": ""}
    shift_job_data = Shift.get_shift_job_data(doctor_profile_id, cash_register_id)
    operator_data, cash_register_data, uuid_data = shift_job_data["operator_data"], shift_job_data["cash_register_data"], shift_job_data["uuid_data"]
    check_cash_register = cash_req.check_cash_register(cash_register_data)
    if check_cash_register["ok"]:
        job_result = cash_req.close_shift(uuid_data, cash_register_data, operator_data)
        if job_result["ok"]:
            Shift.close_shift(uuid_data, cash_register_id, doctor_profile_id)
        else:
            result = job_result
    else:
        result = check_cash_register
    return result


def get_shift_data(doctor_profile_id: int):
    """Проверка статуса смены: открывается, открыта, закрывается, закрыта"""
    data = {"shiftId": None, "cashRegisterId": None, "cashRegisterTitle": "", "open_at": None, "status": "Закрыта"}
    result = {"ok": True, "message": "", "data": data}
    shift: Shift = Shift.objects.filter(operator_id=doctor_profile_id, close_status=False).select_related('cash_register').last()
    if shift:
        shift_status = shift.get_shift_status()
        current_status = shift_status["status"]
        uuid_data = shift_status["uuid"]
        open_at = ""
        if shift.open_at:
            open_at = shift.open_at.astimezone(pytz.timezone(TIME_ZONE)).strftime('%d.%m.%Y %H:%M')
        result["data"] = {"shiftId": shift.pk, "cashRegisterId": shift.cash_register_id, "cashRegisterTitle": shift.cash_register.title, "open_at": open_at, "status": current_status}

        if uuid_data:
            cash_register_data = CashRegister.get_meta_data(cash_register_obj=shift.cash_register)
            check_cash_register = cash_req.check_cash_register(cash_register_data)
            if check_cash_register["ok"]:
                job_result = cash_req.get_job_status(str(uuid_data), cash_register_data)
                if job_result["ok"]:
                    job_status = job_result["data"]["results"][0]
                    if job_status["status"] == "ready":
                        result["data"]["status"] = Shift.change_status(current_status, job_status, shift)
                        open_at = shift.open_at.astimezone(pytz.timezone(TIME_ZONE)).strftime('%d.%m.%Y %H:%M')
                        result["data"]["open_at"] = open_at
                    elif job_status["status"] == "error":
                        result = {"ok": False, "message": "Задача заблокирована на кассе"}
                else:
                    result = job_result
            else:
                result = check_cash_register
    return result


def get_service_coasts(service_ids: list, fin_source_id: int):
    if not service_ids:
        return
    service_ids_tuple = tuple(service_ids)
    service_without_coast = False
    summ = 0
    coasts = []
    services = sql_func.get_services(service_ids_tuple)
    services_coasts = {
        service.id: {
            "id": service.id,
            "title": service.title,
            "coast": 0,
            "discountRelative": service.def_discount,
            "discountAbsolute": 0,
            "discountedCoast": 0,
            "discountStatic": service.prior_discount,
            "count": 1,
            "total": 0
        } for service in services}
    pay_fin_source: IstochnikiFinansirovaniya = IstochnikiFinansirovaniya.objects.filter(pk=fin_source_id).select_related('contracts__price').first()
    price_id = pay_fin_source.contracts.price.pk
    if price_id:
        coasts = sql_func.get_service_coasts(service_ids_tuple, price_id)

    for coast in coasts:
        service_coast = coast.coast
        discount_absolute = service_coast * services_coasts[coast.research_id]["discountRelative"]
        discounted_coast = service_coast - discount_absolute
        services_coasts[coast.research_id]["coast"] = service_coast
        services_coasts[coast.research_id]["discountAbsolute"] = discount_absolute
        services_coasts[coast.research_id]["discountedCoast"] = discounted_coast
        services_coasts[coast.research_id]["total"] = discounted_coast
        summ += coast.coast

    if len(coasts) < len(service_ids):
        service_without_coast = True

    service_coasts = [i for i in services_coasts.values()]

    result = {"coasts": service_coasts, "serviceWithoutCoast": service_without_coast}

    return result


def payment(shift_id, service_coasts, total_coast, cash, received_cash, electronic, card_id):
    result = {"ok": True, "message": "", "cheqId": None}
    shift = Shift.objects.filter(pk=shift_id).select_related('cash_register').first()
    cash_register_data = CashRegister.get_meta_data(cash_register_obj=shift.cash_register)
    uuid_data = str(uuid.uuid4())
    type_operations = Cheque.SELL
    items = ChequeItems.create_items(service_coasts)
    payments = Cheque.create_payments(cash, received_cash, electronic)
    total = total_coast
    job_body = Cheque.create_job_json(cash_register_data, uuid_data, type_operations, items, payments, total)
    check_cash_register = cash_req.check_cash_register(cash_register_data)
    if check_cash_register["ok"]:
        job_result = cash_req.send_job(job_body)
        if job_result["ok"]:
            cheq_id = Cheque.create_cheque(shift_id, type_operations, uuid_data, cash, received_cash, electronic, card_id, items)
            result["cheqId"] = cheq_id
        else:
            result = job_result
    else:
        result = check_cash_register

    return result


def get_cheque_data(cheq_id):
    result = {"ok": True, "message": "", "chequeReady": False}
    cheque = Cheque.objects.filter(pk=cheq_id).select_related('shift', 'shift__cash_register').first()
    if not cheque.cancelled:
        cash_register_data = CashRegister.get_meta_data(cash_register_obj=cheque.shift.cash_register)
        uuid_str = str(cheque.uuid)
        check_cash_register = cash_req.check_cash_register(cash_register_data)
        if check_cash_register["ok"]:
            job_result = cash_req.get_job_status(uuid_str, cash_register_data)
            if job_result["ok"]:
                job_status = job_result["data"]["results"][0]
                if job_status["status"] == "ready":
                    time = current_time()
                    cheque.status = True
                    cheque.payment_at = time
                    cheque.row_data["status"] = True,
                    cheque.row_data["payment_at"] = time
                    cheque.save()
                    result["chequeReady"] = True
                elif job_status["status"] == "error":
                    cheque.cancelled = True
                    result = {"ok": False, "message": f"Задача заблокирована на кассе: {job_status['error']['description']}"}
            else:
                result = job_result
        else:
            result = check_cash_register

    return result
