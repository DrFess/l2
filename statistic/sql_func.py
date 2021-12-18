from django.db import connection
from laboratory.settings import TIME_ZONE, DEATH_RESEARCH_PK
from utils.db import namedtuplefetchall


def direct_job_sql(d_conf, d_s, d_e, fin, can_null):
    """
    парам: d_conf - doctor_confirm, d_s - date-start,  d_e - date-end,  fin - источник финансирвоания

    Вернуть:
    Услуги оказанные врачом за периодн с доп параметрами

    в SQL:
    t_iss - это временная таблица запроса для исследований
    t_card - это временная таблица запроса для карт
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """WITH
        t_iss AS 
            (SELECT directions_napravleniya.client_id, directory_researches.title, directory_researches.code,
            directory_researches.is_first_reception, 
            directions_napravleniya.polis_n, directions_napravleniya.polis_who_give,
            directions_issledovaniya.first_time, directions_issledovaniya.napravleniye_id, 
            directions_issledovaniya.doc_confirmation_id, directions_issledovaniya.def_uet,
            directions_issledovaniya.co_executor_id, directions_issledovaniya.co_executor_uet, 
            directions_issledovaniya.co_executor2_id, directions_issledovaniya.co_executor2_uet,
            directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s AS datetime_confirm,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI:SS') as time_confirm,
            directions_issledovaniya.maybe_onco, statistics_tickets_visitpurpose.title AS purpose,
            directions_issledovaniya.diagnos, statistics_tickets_resultoftreatment.title AS iss_result,
            statistics_tickets_outcomes.title AS outcome
            FROM directions_issledovaniya 
            LEFT JOIN directory_researches
            ON directions_issledovaniya.research_id = directory_researches.id
            LEFT JOIN directions_napravleniya 
            ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
            LEFT JOIN statistics_tickets_visitpurpose
            ON directions_issledovaniya.purpose_id=statistics_tickets_visitpurpose.id 
            LEFT JOIN statistics_tickets_resultoftreatment
            ON directions_issledovaniya.result_reception_id=statistics_tickets_resultoftreatment.id
            LEFT JOIN statistics_tickets_outcomes
            ON directions_issledovaniya.outcome_illness_id=statistics_tickets_outcomes.id
            WHERE (%(d_confirms)s in (directions_issledovaniya.doc_confirmation_id, directions_issledovaniya.co_executor_id,
            directions_issledovaniya.co_executor2_id)) 
            AND time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            AND directory_researches.is_slave_hospital=FALSE AND directory_researches.is_hospital=FALSE
            AND 
            CASE when %(can_null)s = 1 THEN 
            directions_napravleniya.istochnik_f_id = %(ist_fin)s or directions_napravleniya.istochnik_f_id is NULL
            when %(can_null)s = 0 THEN
            directions_napravleniya.istochnik_f_id = %(ist_fin)s
            END 
            
            ORDER BY datetime_confirm),
        t_card AS 
            (SELECT DISTINCT ON (clients_card.id) clients_card.id, clients_card.number AS card_number, 
            clients_individual.family AS client_family, clients_individual.name AS client_name,
            clients_individual.patronymic AS client_patronymic, to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday 
            FROM clients_individual
            LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id
            ORDER BY clients_card.id)
        
        SELECT title, code, is_first_reception, polis_n, polis_who_give, first_time, napravleniye_id, doc_confirmation_id, 
        def_uet, co_executor_id, co_executor_uet, co_executor2_id, co_executor2_uet, datetime_confirm, date_confirm, time_confirm,
        maybe_onco, purpose, diagnos, iss_result, outcome, card_number, client_family, client_name, client_patronymic, birthday FROM t_iss
        LEFT JOIN t_card ON t_iss.client_id=t_card.id
        ORDER BY datetime_confirm""",
            params={'d_confirms': d_conf, 'd_start': d_s, 'd_end': d_e, 'ist_fin': fin, 'can_null': can_null, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def indirect_job_sql(d_conf, d_s, d_e):
    """
    парам:  d_conf - doctor_confirm, d_s - date-start, d_e - date-end

    Вернуть косвенные работы:
    дата, вид работы, всего(УЕТ за дату)

    В SQL:
    t_j - это временная таблица запроса для исследований
    ej - сокращенное наименование от employeejob
    tj - сокращенное наименование от directions_typejob
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """WITH 
        t_j AS 
            (SELECT ej.type_job_id, ej.count, ej.date_job AT TIME ZONE %(tz)s as date_job , tj.value, tj.title as title, 
            (ej.count*tj.value) as total
            FROM public.directions_employeejob ej
            LEFT JOIN public.directions_typejob tj ON ej.type_job_id=tj.id
            WHERE ej.doc_execute_id=%(d_confirms)s AND ej.date_job AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            ORDER BY ej.date_job, ej.type_job_id)

        SELECT date_job, title, SUM(total) FROM t_j
        GROUP BY title, date_job
        ORDER BY date_job """,
            params={'d_confirms': d_conf, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def total_report_sql(d_conf, d_s, d_e, fin):
    """
    Возврат (нагрузку) в порядке:
    research_id, date_confirm, doc_confirmation_id, def_uet, co_executor_id, co_executor_uet,
    co_executor2_id, co_executor2_uet, research_id, research_title, research-co_executor_2_title
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """WITH 
        iss_doc AS
           (SELECT directions_napravleniya.id, d_iss.id as iss_id, d_iss.research_id, EXTRACT(DAY FROM d_iss.time_confirmation) AS date_confirm, d_iss.doc_confirmation_id, d_iss.def_uet,
           d_iss.co_executor_id, d_iss.co_executor_uet, d_iss.co_executor2_id, d_iss.co_executor2_uet, d_iss.napravleniye_id
           FROM public.directions_issledovaniya d_iss
           LEFT JOIN directions_napravleniya 
           ON d_iss.napravleniye_id=directions_napravleniya.id
           WHERE 
           (%(d_confirms)s IN (d_iss.doc_confirmation_id, d_iss.co_executor_id, d_iss.co_executor2_id)) 
           AND d_iss.time_confirmation AT TIME ZONE %(tz)s BETWEEN  %(d_start)s AND %(d_end)s AND directions_napravleniya.istochnik_f_id=%(ist_fin)s
           ORDER BY date_confirm),  
        t_res AS 
           (SELECT d_res.id, d_res.title, co_executor_2_title
           FROM public.directory_researches d_res)

        SELECT iss_doc.iss_id, iss_doc.research_id, iss_doc.date_confirm, iss_doc.doc_confirmation_id, iss_doc.def_uet,
        iss_doc.co_executor_id, iss_doc.co_executor_uet, iss_doc.co_executor2_id, iss_doc.co_executor2_uet,
        t_res.id, t_res.title, t_res.co_executor_2_title
        FROM iss_doc
        LEFT JOIN t_res ON iss_doc.research_id = t_res.id
        ORDER BY iss_doc.date_confirm""",
            params={'d_confirms': d_conf, 'd_start': d_s, 'd_end': d_e, 'ist_fin': fin, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def passed_research(d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """ WITH
        t_iss AS
            (SELECT directions_napravleniya.client_id, directory_researches.title,
            directions_napravleniya.polis_n, directions_napravleniya.polis_who_give,
            directions_issledovaniya.napravleniye_id, 
            to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY-HH24:MI:SS') AS t_confirm,
            to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY-HH24:MI:SS') AS create_napr,
            to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI:SS') AS time_napr,
            directions_issledovaniya.diagnos, statistics_tickets_resultoftreatment.title as result, 
            directions_issledovaniya.id AS iss_id, directions_napravleniya.data_sozdaniya
            FROM directions_issledovaniya
            LEFT JOIN directory_researches 
                ON directions_issledovaniya.research_id = directory_researches.Id
            LEFT JOIN directions_napravleniya 
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
            LEFT JOIN statistics_tickets_resultoftreatment 
                ON directions_issledovaniya.result_reception_id=statistics_tickets_resultoftreatment.id
            WHERE directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s 
            AND directions_issledovaniya.time_confirmation IS NOT NULL
            AND TRUE IN (directory_researches.is_paraclinic, directory_researches.is_doc_refferal, 
            directory_researches.is_stom, directory_researches.is_hospital)
            ),
        t_card AS
            (SELECT DISTINCT ON (clients_card.id) clients_card.id, clients_card.number as num_card, clients_individual.family,
            clients_individual.name AS ind_name, clients_individual.patronymic, to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday,
            clients_document.number, clients_document.serial, clients_document.who_give, clients_card.main_address,
            clients_card.fact_address, clients_card.work_place
            FROM clients_individual
            LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id
            LEFT JOIN clients_document ON clients_card.individual_id = clients_document.individual_id
            WHERE clients_document.document_type_id = (SELECT id AS polis_id FROM clients_documenttype WHERE title = 'Полис ОМС')
            ORDER BY clients_card.id),
            t_field AS
            (SELECT id AS f_is FROM directory_paraclinicinputfield
            WHERE directory_paraclinicinputfield.title='Кем направлен')

        SELECT client_id, title, polis_n, polis_who_give, napravleniye_id, t_confirm, create_napr, diagnos, result, 
        data_sozdaniya, num_card, family, ind_name, patronymic, birthday, main_address, fact_address, work_place, 
        directions_paraclinicresult.value, time_napr FROM t_iss
        LEFT JOIN t_card ON t_iss.client_id = t_card.id
        LEFT JOIN directions_paraclinicresult ON t_iss.iss_id = directions_paraclinicresult.issledovaniye_id
        AND (directions_paraclinicresult.field_id IN (SELECT * FROM t_field))
        ORDER BY client_id, data_sozdaniya""",
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def statistics_research(research_id, d_s, d_e):
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон, fin - источник финансирования
    выход: Физлицо, Дата рождения, Возраст, Карта, Исследование, Источник финансирования, Стоимость, Исполнитель,
        Направление, создано направление(дата), Дата подтверждения услуги, Время подтверждения.
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """ WITH
    t_hosp AS 
        (SELECT id, title FROM hospitals_hospitals),
    t_iss AS
        (SELECT directions_napravleniya.client_id, directions_issledovaniya.napravleniye_id as napr, directions_napravleniya.hospital_id as hospital_id, 
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_confirm,
        to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'HH24:MI:SS') AS time_confirm,
        to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS create_date_napr,
        to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'HH24:MI:SS') AS create_time_napr, 
        directions_issledovaniya.doc_confirmation_id as doc, users_doctorprofile.fio as doc_fio,
        directions_issledovaniya.coast, directions_issledovaniya.discount,
        directions_issledovaniya.how_many, directions_napravleniya.data_sozdaniya, directions_napravleniya.istochnik_f_id,
        directions_istochnikifinansirovaniya.title as ist_f,
        directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation
        FROM directions_issledovaniya
        LEFT JOIN directions_napravleniya 
           ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
        LEFT JOIN users_doctorprofile
           ON directions_issledovaniya.doc_confirmation_id=users_doctorprofile.id
        LEFT JOIN directions_istochnikifinansirovaniya
        ON directions_napravleniya.istochnik_f_id=directions_istochnikifinansirovaniya.id 
        WHERE directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
        AND directions_issledovaniya.research_id=%(research_id)s),
    t_card AS
       (SELECT DISTINCT ON (clients_card.id) clients_card.id, clients_card.number AS num_card, 
        clients_individual.family as ind_family,
        clients_individual.name AS ind_name, clients_individual.patronymic, 
        to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday,
        clients_individual.birthday as date_born
        FROM clients_individual
        LEFT JOIN clients_card ON clients_individual.id = clients_card.individual_id)

        SELECT napr, date_confirm, time_confirm, create_date_napr, create_time_napr, doc_fio, coast, discount, 
        how_many, ((coast + (coast/100 * discount)) * how_many)::NUMERIC(10,2) AS sum_money, ist_f, time_confirmation, num_card, 
        ind_family, ind_name, patronymic, birthday, date_born,
        to_char(EXTRACT(YEAR from age(time_confirmation, date_born)), '999') as ind_age, t_hosp.title FROM t_iss
        LEFT JOIN t_card ON t_iss.client_id = t_card.id
        LEFT JOIN t_hosp ON t_iss.hospital_id = t_hosp.id
        ORDER BY time_confirmation""",
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        row = cursor.fetchall()
    return row


def statistics_death_research(research_id: object, d_s: object, d_e: object) -> object:
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_paraclinicresult.issledovaniye_id,
                directions_paraclinicresult.field_id,
                directory_paraclinicinputfield.title,
                directions_paraclinicresult.value,
                to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS confirm_time,
                directions_paraclinicresult.value_json::json as json_value,
                value_json::jsonb #>> '{rows, 0, 2}' as diag,
                concat(value_json::jsonb #>> '{title}', value_json::jsonb #>> '{rows, 0, 2}') as result,
                directions_issledovaniya.napravleniye_id,
                directions_napravleniya.client_id,
                concat(clients_individual.family, ' ', clients_individual.name, ' ', clients_individual.patronymic) as fio_patient,
                clients_individual.sex,
                hospitals_hospitals.title as hosp_title
                FROM public.directions_paraclinicresult
                LEFT JOIN directions_issledovaniya
                ON directions_issledovaniya.id = directions_paraclinicresult.issledovaniye_id
                LEFT JOIN directory_paraclinicinputfield
                ON directory_paraclinicinputfield.id = directions_paraclinicresult.field_id
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                where issledovaniye_id in (
                SELECT id FROM public.directions_issledovaniya
                where research_id = %(death_research_id)s and (time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s))
                order by issledovaniye_id
            """,
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'death_research_id': DEATH_RESEARCH_PK},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def statistics_reserved_number_death_research(research_id: object, d_s: object, d_e: object) -> object:
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                directions_paraclinicresult.issledovaniye_id,
                directions_paraclinicresult.field_id,
                directory_paraclinicinputfield.title,
                directions_paraclinicresult.value,
                directions_issledovaniya.napravleniye_id,
                directions_napravleniya.client_id,
                to_char(directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_create,
                concat(clients_individual.family, ' ', clients_individual.name, ' ', clients_individual.patronymic) as fio_patient,
                clients_individual.sex,
                hospitals_hospitals.title as hosp_title
                FROM public.directions_paraclinicresult
                LEFT JOIN directions_issledovaniya
                ON directions_issledovaniya.id = directions_paraclinicresult.issledovaniye_id
                LEFT JOIN directory_paraclinicinputfield
                ON directory_paraclinicinputfield.id = directions_paraclinicresult.field_id
                LEFT JOIN directions_napravleniya
                ON directions_napravleniya.id = directions_issledovaniya.napravleniye_id
                LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                where issledovaniye_id in (
                SELECT id FROM public.directions_issledovaniya
                where research_id = %(death_research_id)s and time_confirmation is Null) and directory_paraclinicinputfield.title='Номер' and
                directions_napravleniya.data_sozdaniya AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                order by hospitals_hospitals.title, directions_napravleniya.data_sozdaniya
            """,
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'death_research_id': DEATH_RESEARCH_PK},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def statistics_sum_research_by_lab(podrazdeleniye: tuple, d_s: object, d_e: object) -> object:
    """
    на входе: research_id - id-услуги, d_s- дата начала, d_e - дата.кон
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                    podrazdeleniya_podrazdeleniya.title as lab_title,
                    directory_researches.title as research_title, 
                    COUNT(research_id) as sum_research_id 
                FROM public.directions_issledovaniya
                LEFT JOIN directory_researches
                ON directory_researches.id = directions_issledovaniya.research_id
                LEFT JOIN podrazdeleniya_podrazdeleniya
                ON podrazdeleniya_podrazdeleniya.id = directory_researches.podrazdeleniye_id
                where research_id in (select id from directory_researches WHERE podrazdeleniye_id in %(podrazdeleniye)s) and 
                    time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                GROUP BY directory_researches.title, directory_researches.podrazdeleniye_id, podrazdeleniya_podrazdeleniya.title
                ORDER BY podrazdeleniya_podrazdeleniya.title, directory_researches.title
                            """,
            params={'podrazdeleniye': podrazdeleniye, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def disp_diagnos(diagnos, d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """WITH
            t_iss AS (
            SELECT id, diagnos, illnes, date_start, date_end, why_stop, card_id, 
                        doc_end_reg_id, doc_start_reg_id, spec_reg_id 
            FROM public.clients_dispensaryreg
            WHERE diagnos = 'U999' and (date_start AT TIME ZONE %(tz)s
            BETWEEN %(d_start)s AND %(d_end)s OR date_end AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s)
            ORDER BY date_start DESC),
            t_card AS (SELECT id as card_id, individual_id, number as num_card from clients_card WHERE id in (SELECT card_id from t_iss)),
            
            t_ind AS (SELECT family as p_family, name as p_name, patronymic as p_patr, birthday, t_card.card_id, t_card.num_card 
                  FROM clients_individual
            LEFT JOIN t_card ON t_card.individual_id = id 
            where id in (SELECT individual_id from t_card)),
            
            t_doc_start AS (SELECT id as docstart_id, fio from users_doctorprofile where id in (SELECT doc_start_reg_id from t_iss) ),
            t_doc_end AS (SELECT id as docend_id, fio from users_doctorprofile where id in (SELECT doc_end_reg_id from t_iss) )
            
            SELECT concat(p_family, ' ', p_name, ' ', p_patr) as patient, 
            to_char(t_ind.birthday, 'DD.MM.YYYY') as birthday,
            t_ind.num_card, 
            t_doc_start.fio as doc_start, 
            to_char(date_start, 'DD.MM.YYYY') as date_start,
            t_doc_end.fio as doc_stop, 
            to_char(date_end, 'DD.MM.YYYY') as date_end
            FROM t_iss
            LEFT JOIN t_ind ON t_iss.card_id = t_ind.card_id
            LEFT JOIN t_doc_start ON t_iss.doc_start_reg_id = t_doc_start.docstart_id
            LEFT JOIN t_doc_end ON t_iss.doc_end_reg_id = t_doc_end.docend_id
            ORDER by patient
            """,
            params={'diagnos': diagnos, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )
        row = cursor.fetchall()
    return row


def message_ticket(hospitals_id, d_s, d_e):
    """
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
            SELECT 
                doctor_call_doctorcall.id as num,
                doctor_call_doctorcall.external_num,
                to_char(doctor_call_doctorcall.create_at AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_create,
                doctor_call_doctorcall.comment,
                doctor_call_doctorcall.phone,
                doctor_call_doctorcall.address,
                doctor_call_doctorcall.email,	  
                doc_call_hospital.title as hospital_title,
                doc_call_hospital.short_title as hospital_short_title,
                doctor_call_doctorcall.purpose,
                doctor_call_doctorcall.status,
                clients_individual.name,
                clients_individual.family,
                clients_individual.patronymic,
                to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday,
                doctor_call_doctorcall.hospital_id as hospital_id,
                doctor_call_doctorcall.is_external,
                users_doctorprofile.fio,
                who_create_hospital.short_title
                FROM doctor_call_doctorcall
                LEFT JOIN hospitals_hospitals as doc_call_hospital ON (doc_call_hospital.id=doctor_call_doctorcall.hospital_id)
                LEFT JOIN clients_card ON clients_card.id=doctor_call_doctorcall.client_id
                LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                LEFT JOIN users_doctorprofile ON users_doctorprofile.id=doctor_call_doctorcall.doc_who_create_id
                LEFT JOIN hospitals_hospitals as who_create_hospital ON (who_create_hospital.id=users_doctorprofile.hospital_id)
                WHERE doctor_call_doctorcall.create_at AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s 
                AND doctor_call_doctorcall.hospital_id = ANY(%(hospitals_id)s)
                ORDER BY doctor_call_doctorcall.hospital_id, doctor_call_doctorcall.create_at 
 
            """,
            params={'hospitals_id': hospitals_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def message_ticket_purpose_total(hospitals_id, d_s, d_e):
    """
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """ 
            WITH 
                total_doc_call AS (
                  SELECT
                  purpose as total_purpose, 
                  COUNT(purpose) as sum_total_purpose
                  FROM doctor_call_doctorcall as total_dc
                  WHERE create_at AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s AND total_dc.hospital_id = ANY(%(hospitals_id)s)
                  GROUP BY purpose
                ),
                
                execut_doc_call AS (
                  SELECT purpose as execute_purpose, 
                  COUNT(purpose) as sum_execute_purpose
                  FROM doctor_call_doctorcall as exec_dc
                  WHERE create_at AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s AND STATUS=3 AND exec_dc.hospital_id = ANY(%(hospitals_id)s)
                  GROUP BY purpose)
                
                SELECT total_purpose, sum_total_purpose, execute_purpose, sum_execute_purpose
                    FROM total_doc_call
                    LEFT JOIN execut_doc_call ON execut_doc_call.execute_purpose = total_doc_call.total_purpose
            """,
            params={'hospitals_id': hospitals_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def attached_female_on_month(last_day_month_for_age, min_age, max_age):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(id) FROM clients_card
            WHERE clients_card.individual_id IN 
              (SELECT id FROM clients_individual WHERE (date_part('year', age(%(last_day_month_for_age)s, birthday))::int BETWEEN %(min_age)s and %(max_age)s) and sex='ж')
            """,
            params={
                'last_day_month_for_age': last_day_month_for_age,
                'min_age': min_age,
                'max_age': max_age,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def screening_plan_for_month_all_count(date_plan_year, date_plan_month):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(DISTINCT card_id) FROM public.clients_screeningregplan
            WHERE date_part('year', clients_screeningregplan.date)::int = %(date_plan_year)s AND
            date_part('month', clients_screeningregplan.date)::int = %(date_plan_month)s
            """,
            params={
                'date_plan_year': date_plan_year,
                'date_plan_month': date_plan_month,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def screening_plan_for_month_all_patient(date_plan_year, date_plan_month):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT ON (card_id) card_id FROM public.clients_screeningregplan
            WHERE date_part('year', clients_screeningregplan.date)::int = %(date_plan_year)s AND
            date_part('month', clients_screeningregplan.date)::int = %(date_plan_month)s
            """,
            params={
                'date_plan_year': date_plan_year,
                'date_plan_month': date_plan_month,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def must_dispensarization_from_screening_plan_for_month(year, month, date_dispansarization):
    with connection.cursor() as cursor:
        cursor.execute(
            """
          SELECT count(distinct dispensarisation.card_id) FROM 
            (SELECT 
                  clients_screeningregplan.card_id, 
                  directory_dispensaryroutesheet.research_id as dispensarisation_research
                FROM clients_screeningregplan
                LEFT JOIN clients_card
                ON clients_card.id=clients_screeningregplan.card_id
            
                LEFT JOIN clients_individual
                ON clients_individual.id=clients_card.individual_id
                LEFT JOIN directory_dispensaryroutesheet
                ON 
                  clients_screeningregplan.research_id=directory_dispensaryroutesheet.research_id AND
                  directory_dispensaryroutesheet.age_client = date_part('year', age(%(date_dispansarization)s, clients_individual.birthday))::int AND
                  clients_individual.sex = directory_dispensaryroutesheet.sex_client
                WHERE date_part('year', clients_screeningregplan.date)::int = %(screening_date_plan_year)s AND
                date_part('month', clients_screeningregplan.date)::int = %(screening_date_plan_month)s
                ORDER BY clients_screeningregplan.card_id) dispensarisation
                WHERE dispensarisation.dispensarisation_research is NOT NULL
            """,
            params={
                'screening_date_plan_year': year,
                'screening_date_plan_month': month,
                'date_dispansarization': date_dispansarization,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_pass_screening(year, month, start_time_confirm, end_time_confirm, list_card):
    if not list_card:
        return []

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(distinct client_result.client_id) FROM 
                (SELECT
                    distinct on (directions_napravleniya.client_id, directions_issledovaniya.research_id)
                    date_part('year', directions_issledovaniya.time_confirmation) as year_date,
                    date_part('month', directions_issledovaniya.time_confirmation) as month_date,
                    date_part('day', directions_issledovaniya.time_confirmation) as day_date, 
                    directions_issledovaniya.id as iss_id, 
                    directions_napravleniya.client_id as client_id, 
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id as research_id,
                    directions_issledovaniya.time_confirmation as confirm
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                WHERE 
                    directions_napravleniya.client_id in %(list_card)s
                AND
                    directions_issledovaniya.research_id in (SELECT 
                        distinct on (clients_screeningregplan.research_id) clients_screeningregplan.research_id 
                        FROM clients_screeningregplan WHERE date_part('year', clients_screeningregplan.date)::int = %(screening_date_plan_year)s AND
                        date_part('month', clients_screeningregplan.date)::int = %(screening_date_plan_month)s) 
                AND
                    (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_time_confirm)s AND %(end_time_confirm)s)
                ORDER BY 
                    directions_napravleniya.client_id, 
                    directions_issledovaniya.research_id, 
                    directions_issledovaniya.time_confirmation DESC) client_result
            """,
            params={
                'screening_date_plan_year': year,
                'screening_date_plan_month': month,
                'start_time_confirm': start_time_confirm,
                'end_time_confirm': end_time_confirm,
                'list_card': list_card,
                'tz': TIME_ZONE,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_pass_screening_in_dispensarization(year, month, start_time_confirm, end_time_confirm, date_dispansarization):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT count(distinct client_result.client_id) FROM 
                    (SELECT
                        distinct on (directions_napravleniya.client_id, directions_issledovaniya.research_id)
                        directions_napravleniya.client_id as client_id, 
                        directions_issledovaniya.napravleniye_id as dir_id,
                        directions_issledovaniya.research_id as research_id,
                        directions_issledovaniya.time_confirmation as confirm
                    FROM directions_issledovaniya
                    LEFT JOIN directions_napravleniya
                    ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                    WHERE 
                        directions_napravleniya.client_id in 
                        (
                            SELECT distinct ON (dispensarisation_card.card_id) dispensarisation_card.card_id FROM 
                                (
                                    SELECT clients_screeningregplan.card_id, directory_dispensaryroutesheet.research_id as dispensarisation_research
                                        FROM clients_screeningregplan
                                        LEFT JOIN clients_card
                                        ON clients_card.id=clients_screeningregplan.card_id
                                        
                                        LEFT JOIN clients_individual
                                        ON clients_individual.id=clients_card.individual_id
                                        LEFT JOIN directory_dispensaryroutesheet
                                        ON 
                                        clients_screeningregplan.research_id=directory_dispensaryroutesheet.research_id AND
                                        directory_dispensaryroutesheet.age_client = date_part('year', age(%(date_dispansarization)s, clients_individual.birthday))::int AND
                                        clients_individual.sex = directory_dispensaryroutesheet.sex_client
                                    WHERE date_part('year', clients_screeningregplan.date)::int = %(screening_date_plan_year)s AND
                                          date_part('month', clients_screeningregplan.date)::int = %(screening_date_plan_month)s
                                    ORDER BY clients_screeningregplan.card_id
                                ) dispensarisation_card
                            WHERE dispensarisation_card.dispensarisation_research is NOT NULL
                        )
                    AND
                        directions_issledovaniya.research_id in 
                        (
                            SELECT distinct on (dispensarisation.research_id) dispensarisation.research_id FROM
                                (
                                    SELECT  directory_dispensaryroutesheet.research_id, directory_dispensaryroutesheet.research_id as dispensarisation_research
                                        FROM clients_screeningregplan
                                        LEFT JOIN clients_card
                                        ON clients_card.id=clients_screeningregplan.card_id
                                        
                                        LEFT JOIN clients_individual
                                        ON clients_individual.id=clients_card.individual_id
                                        LEFT JOIN directory_dispensaryroutesheet
                                        ON 
                                        clients_screeningregplan.research_id=directory_dispensaryroutesheet.research_id AND
                                        directory_dispensaryroutesheet.age_client = date_part('year', age(%(date_dispansarization)s, clients_individual.birthday))::int AND
                                        clients_individual.sex = directory_dispensaryroutesheet.sex_client
                                    WHERE date_part('year', clients_screeningregplan.date)::int = %(screening_date_plan_year)s AND
                                          date_part('month', clients_screeningregplan.date)::int = %(screening_date_plan_month)s
                                    ORDER BY clients_screeningregplan.card_id
                                ) dispensarisation
                                WHERE dispensarisation.dispensarisation_research is NOT NULL
                        ) 
                    AND
                    (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_time_confirm)s AND %(end_time_confirm)s)  
                    ORDER BY directions_napravleniya.client_id, directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation DESC) client_result
            """,
            params={
                'screening_date_plan_year': year,
                'screening_date_plan_month': month,
                'start_time_confirm': start_time_confirm,
                'end_time_confirm': end_time_confirm,
                'date_dispansarization': date_dispansarization,
                'tz': TIME_ZONE,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_pass_pap_analysis_count(start_time_confirm, end_time_confirm, list_card, pap_id_analysis):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(distinct result_papa.client_id) FROM
                (SELECT
                    distinct on (directions_napravleniya.client_id, directions_issledovaniya.research_id)
                    directions_napravleniya.client_id as client_id, 
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id as research_id,
                    directions_issledovaniya.time_confirmation as confirm
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                WHERE 
                directions_napravleniya.client_id in %(list_card)s
                AND
                directions_issledovaniya.research_id in %(pap_id_analysis)s
                AND
                (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_time_confirm)s AND %(end_time_confirm)s)  
                ORDER BY directions_napravleniya.client_id, directions_issledovaniya.research_id, directions_issledovaniya.time_confirmation DESC)
            result_papa  
            """,
            params={'start_time_confirm': start_time_confirm, 'end_time_confirm': end_time_confirm, 'list_card': list_card, 'pap_id_analysis': pap_id_analysis, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_pass_pap_fraction_result_value(start_time_confirm, end_time_confirm, list_card, pap_id_analysis, fraction_id, value_result1, value_result2="", count_param=1):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(distinct client_result.client_id) FROM 
                (SELECT
                distinct on (directions_napravleniya.client_id, directions_issledovaniya.research_id)
                directions_napravleniya.client_id as client_id, 
                directions_issledovaniya.napravleniye_id as dir_id,
                directions_issledovaniya.research_id as research_id,
                directions_issledovaniya.time_confirmation as confirm,
                directions_result.value,
                directions_result.fraction_id
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                LEFT JOIN directions_result
                ON directions_result.issledovaniye_id=directions_issledovaniya.id 
                WHERE 
                directions_napravleniya.client_id in %(list_card)s
                AND
                directions_issledovaniya.research_id in %(pap_id_analysis)s
                AND
                (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_time_confirm)s AND %(end_time_confirm)s)
                AND
                directions_result.fraction_id in %(fraction_id)s
                AND 
                    CASE WHEN %(count_param)s > 1 THEN
                      directions_result.value ~ %(value_result1)s or directions_result.value ~ %(value_result2)s
                    ELSE
                      directions_result.value ~ %(value_result1)s
                    END
                ORDER BY directions_napravleniya.client_id, 
                directions_issledovaniya.research_id, 
                directions_issledovaniya.time_confirmation DESC) 
            client_result
            """,
            params={
                'start_time_confirm': start_time_confirm,
                'end_time_confirm': end_time_confirm,
                'list_card': list_card,
                'pap_id_analysis': pap_id_analysis,
                'fraction_id': fraction_id,
                'tz': TIME_ZONE,
                'count_param': count_param,
                'value_result1': value_result1,
                'value_result2': value_result2,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_card_dublicate_pass_pap_fraction_not_not_enough_adequate_result_value(
    start_time_confirm, end_time_confirm, list_card, pap_id_analysis, fraction_id, value_result1, value_result2="", count_param=1
):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT client_result.client_id FROM
             (SELECT
                directions_napravleniya.client_id as client_id
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                LEFT JOIN directions_result
                ON directions_result.issledovaniye_id=directions_issledovaniya.id 
                WHERE 
                directions_napravleniya.client_id in %(list_card)s
                AND
                directions_issledovaniya.research_id in %(pap_id_analysis)s
                AND
                (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(start_time_confirm)s AND %(end_time_confirm)s)
                AND
                directions_result.fraction_id in %(fraction_id)s
                AND 
                    CASE WHEN %(count_param)s > 1 THEN
                      directions_result.value ILIKE %(value_result1)s or  directions_result.value ILIKE %(value_result2)s
                    ELSE
                      directions_result.value ILIKE %(value_result1)s
                    END
                ORDER BY directions_napravleniya.client_id, 
                directions_issledovaniya.research_id, 
                directions_issledovaniya.time_confirmation) client_result
                group by client_result.client_id having count(client_result.client_id)>1
            """,
            params={
                'start_time_confirm': start_time_confirm,
                'end_time_confirm': end_time_confirm,
                'list_card': list_card,
                'pap_id_analysis': pap_id_analysis,
                'fraction_id': fraction_id,
                'tz': TIME_ZONE,
                'count_param': count_param,
                'value_result1': value_result1,
                'value_result2': value_result2,
            },
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sql_get_result_by_direction(pk, d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT
                    directions_napravleniya.client_id as client_id, 
                    directions_napravleniya.data_sozdaniya,
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id as research_id,
                    directions_issledovaniya.time_confirmation as confirm,
                    clients_individual.family,
                    clients_individual.name,
                    clients_individual.patronymic,
                    clients_individual.birthday,
                    clients_individual.sex,
                    directions_result.id,
                    directions_result.value,
                    directions_result.fraction_id,
                    hospitals_hospitals.title as hosp_title,
                    hospitals_hospitals.ogrn as hosp_ogrn
                    FROM directions_issledovaniya
                    LEFT JOIN directions_napravleniya
                    ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                    LEFT JOIN directions_result
                    ON directions_result.issledovaniye_id=directions_issledovaniya.id
                    LEFT JOIN clients_card ON clients_card.id=directions_napravleniya.client_id
                    LEFT JOIN clients_individual ON clients_individual.id=clients_card.individual_id
                    LEFT JOIN hospitals_hospitals on directions_napravleniya.hospital_id = hospitals_hospitals.id
                    WHERE
                        directions_issledovaniya.research_id = %(pk)s
                    AND
                    (directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s)
                            """,
            params={'pk': pk, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows


def sql_get_documents_by_card_id(card_tuple):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                clients_carddocusage.document_id,
                clients_carddocusage.card_id,
                clients_document.id,
                clients_document.serial,
                clients_document.number,
                clients_document.is_active,
                clients_document.document_type_id
            FROM clients_carddocusage 
            LEFT JOIN  clients_document on clients_document.id=clients_carddocusage.document_id
            WHERE clients_carddocusage.card_id in %(cards)s
            """,
            params={'cards': card_tuple, },
        )

        rows = namedtuplefetchall(cursor)
    return rows
