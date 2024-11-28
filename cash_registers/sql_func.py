from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_cash_registers():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM cash_registers_cashregister
            """,
        )
        rows = namedtuplefetchall(cursor)
    return rows


def check_shift(cash_register_id, doctor_profile_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
            operator_id,
            cash_register_id,
            close_status
            FROM cash_registers_shift
            WHERE
            (operator_id=%(doctor_profile_id)s or cash_register_id=%(cash_register_id)s)
            and
            close_status = False
            """,
            params={"cash_register_id": cash_register_id, "doctor_profile_id": doctor_profile_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_service_coasts(services_ids, price_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            contracts_pricecoast.coast, 
            contracts_pricecoast.research_id
            FROM contracts_pricecoast
            WHERE 
            contracts_pricecoast.price_name_id = %(price_id)s and 
            contracts_pricecoast.research_id in %(services_ids)s
            """,
            params={"services_ids": services_ids, "price_id": price_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_services(services_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT directory_researches.id, directory_researches.title, directory_researches.def_discount, directory_researches.prior_discount FROM directory_researches
            WHERE directory_researches.id in %(services_ids)s
            """,
            params={"services_ids": services_ids},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_services_by_directions(directions_ids, fin_source_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            directions_napravleniya.id as direction_id,
            directory_researches.id,
            directory_researches.title,
            directory_researches.def_discount,
            directory_researches.prior_discount
            FROM directions_napravleniya
            INNER JOIN directions_issledovaniya on directions_napravleniya.id = directions_issledovaniya.napravleniye_id
            INNER JOIN directory_researches on directions_issledovaniya.research_id = directory_researches.id
            WHERE directions_napravleniya.id in %(directions_ids)s AND
            directions_napravleniya.istochnik_f_id = %(fin_source_id)s
            """,
            params={"directions_ids": directions_ids, "fin_source_id": fin_source_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_total_count_issledovania(directions_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            count(*)
            
            FROM directions_napravleniya
            INNER JOIN directions_issledovaniya on directions_napravleniya.id = directions_issledovaniya.napravleniye_id
            
            WHERE directions_napravleniya.id in %(directions_ids)s
            """,
            params={"directions_ids": directions_ids},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_patient_cheque(date_start, date_end, patient_card_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 

            *

            FROM cash_registers_cheque

            WHERE cash_registers_cheque.created_at AT TIME ZONE %(tz)s BETWEEN %(date_start)s AND %(date_end)s
            AND cash_registers_cheque.card_id = %(patient_card_pk)s

            ORDER BY created_at DESC
            """,
            params={"tz": TIME_ZONE, "date_start": date_start, "date_end": date_end, "patient_card_pk": patient_card_pk},
        )
        rows = namedtuplefetchall(cursor)
    return rows
