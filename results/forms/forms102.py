from utils.dates import normalize_date
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import directory.models as directory
from directions.models import ParaclinicResult
from appconf.manager import SettingManager
from results.prepare_data import text_to_bold, fields_result_only_title_fields


def form_01(direction, iss, fwb, doc, leftnone, user=None):
    # ПАТОЛОГО-АНАТОМИЧЕСКОЕ заключение
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "FreeSans"
    style.fontSize = 10
    style.alignment = TA_JUSTIFY

    style_ml = deepcopy(style)
    style_ml.leftIndent = 5 * mm
    style_ml.spaceAfter = 0.5 * mm

    styleBold = deepcopy(style)
    styleBold.fontName = "FreeSansBold"

    hospital_name = SettingManager.get("org_title")
    hospital_address = SettingManager.get("org_address")
    hospital_kod_ogrn = SettingManager.get("org_ogrn")

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm

    opinion = [
        [
            Paragraph(f'<font size=10>{hospital_name}<br/>Адрес: {hospital_address}<br/>ОГРН: {hospital_kod_ogrn} <br/> </font>', styleT),
            Paragraph('<font size=9 >Медицинская документация <br/> Учетная форма № 014/1-у<br/>Утверждена приказом Минздрава России<br/>от 24 марта 2016г. № 179н</font>', styleT),
        ],
    ]

    tbl = Table(opinion, 2 * [100 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                ('LEFTPADDING', (1, 0), (-1, -1), 35 * mm),
                ('LEFTPADDING', (0, 0), (0, -1), 15 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
    )

    fwb.append(tbl)
    fwb.append(Spacer(1, 5 * mm))

    history_num = ''
    if direction.parent and direction.parent.research.is_hospital:
        history_num = f"(cтационар-{str(direction.parent.napravleniye_id)})"

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 11.5
    styleCenterBold.leading = 15
    styleCenterBold.fontName = 'FreeSansBold'

    fwb.append(Paragraph(f'ПРОТОКОЛ № {direction.pk} {history_num} ', styleCenterBold))
    fwb.append(Paragraph('ПРИЖИЗНЕННОГО ПАТОЛОГО-АНАТОМИЧЕСКОГО<br/> ИССЛЕДОВАНИЯ БИОПСИЙНОГО (ОПЕРАЦИОННОГО) МАТЕРИАЛА', styleCenterBold))
    short_title = iss.research.short_title
    fwb.append(Paragraph(f'{short_title.upper()}', styleCenterBold))

    open_bold_tag = "<font face =\"FreeSansBold\">"
    close_tag_bold = "</font>"

    fwb.append(Spacer(1, 4 * mm))
    fwb.append(Paragraph(f'{open_bold_tag}1. Отделение, направившее биопсийный (операционный) материал:{close_tag_bold}{direction.doc.podrazdeleniye.title}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}2. Фамилия, имя, отчество (при наличии) пациента:{close_tag_bold} {direction.client.individual.fio()}', style_ml))
    sex = direction.client.individual.sex
    if sex == "м":
        sex = f'{sex}-1'
    else:
        sex = f'{sex}-2'
    space_symbol = '&nbsp;'
    fwb.append(Paragraph(f'{open_bold_tag}3. Пол:{close_tag_bold} {sex}, {space_symbol * 5} {open_bold_tag}4. Дата рождения:{close_tag_bold} {direction.client.individual.bd()}', style_ml))
    polis_num = ''
    polis_issue = ''
    snils = ''
    ind_data = direction.client.get_data_individual()
    if ind_data['oms']['polis_num']:
        polis_num = ind_data['oms']['polis_num']
    if ind_data['oms']['polis_issued']:
        polis_issue = ind_data['oms']['polis_issued']
    if ind_data['snils']:
        snils = ind_data['snils']
    fwb.append(Paragraph(f'{open_bold_tag}5. Полис ОМС:{close_tag_bold}{polis_num}-{polis_issue} {space_symbol * 4} {open_bold_tag}6. СНИЛС:{close_tag_bold} {snils}', style_ml))
    address = ind_data['main_address']
    fwb.append(Paragraph(f'{open_bold_tag}7. Место регистрации:{close_tag_bold} {address}', style_ml))
    fwb.append(Paragraph(f'{open_bold_tag}8. Местность:{close_tag_bold} городская — 1, сельская — 2.', style_ml))

    for group in directory.ParaclinicInputGroups.objects.filter(research=iss.research).order_by("order"):
        results = ParaclinicResult.objects.filter(issledovaniye=iss, field__group=group).order_by("field__order")
        group_title = False
        if results.exists():
            fwb.append(Spacer(1, 1 * mm))
            if group.show_title and group.show_title != "":
                fwb.append(Paragraph(group.title.replace('<', '&lt;').replace('>', '&gt;'), styleBold))
                fwb.append(Spacer(1, 0.25 * mm))
                group_title = True
            for r in results:
                field_type = r.get_field_type()
                if field_type == 15:
                    continue
                else:
                    v = r.value.replace('<', '&lt;').replace('>', '&gt;').replace("\n", "<br/>")
                    v = v.replace('&lt;sub&gt;', '<sub>')
                    v = v.replace('&lt;/sub&gt;', '</sub>')
                    v = v.replace('&lt;sup&gt;', '<sup>')
                    v = v.replace('&lt;/sup&gt;', '</sup>')
                    v = text_to_bold(v)
                    if field_type == 16:
                        continue
                    if field_type == 17:
                        continue
                    if field_type == 1:
                        v = normalize_date(v)
                    if field_type in [11, 13]:
                        v = '<font face="FreeSans" size="8">{}</font>'.format(v.replace("&lt;br/&gt;", " "))
                    if r.field.get_title(force_type=field_type) != "":
                        fwb.append(
                            Paragraph(
                                "<font face=\"FreeSansBold\">{}:</font>{}".format(r.field.get_title(force_type=field_type).replace('<', '&lt;').replace('>', '&gt;'), v),
                                style_ml if group_title else style,
                            )
                        )
                    else:
                        fwb.append(Paragraph(v, style))

    return fwb
