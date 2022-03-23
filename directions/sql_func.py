from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def check_limit_assign_researches(district_group_id,):

    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT users_districtresearchlimitassign.id, 
                users_districtresearchlimitassign.limit_count, 
                users_districtresearchlimitassign.type_period_limit,
                users_districtresearchlimitassign_research.researches_id,
                users_districtresearchlimitassign.district_group_id
                from users_districtresearchlimitassign 
                LEFT JOIN users_districtresearchlimitassign_research ON
                users_districtresearchlimitassign.id = users_districtresearchlimitassign_research.districtresearchlimitassign_id
                where
                district_group_id = %(district_group_id)s
            """,
            params={'district_group_id': district_group_id},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def get_count_researches_by_doc(doctor_pks,  d_s, d_e):

    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                directions_issledovaniya.research_id,
                count(directions_napravleniya.id) as count
                FROM directions_napravleniya
                LEFT JOIN directions_issledovaniya
                ON directions_napravleniya.id=directions_issledovaniya.napravleniye_id
                WHERE doc_who_create_id in %(doctor_pks)s and data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                group by directions_issledovaniya.research_id
            """,
            params={'doctor_pks': doctor_pks, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows
