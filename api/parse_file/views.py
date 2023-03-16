import json
import tempfile
from django.http import HttpRequest, JsonResponse

from api.models import Application
from api.parse_file.pdf import extract_text_from_pdf
import simplejson as json

from api.views import endpoint
from openpyxl import load_workbook
from appconf.manager import SettingManager
from integration_framework.views import check_enp
from api.patients.views import patients_search_card


def dnk_covid(request):
    prefixes = []
    key_dnk = SettingManager.get("dnk_kovid", default='false', default_type='s')
    to_return = None
    for x in "ABCDEF":
        prefixes.extend([f"{x}{i}" for i in range(1, 13)])
    file = request.FILES['file']
    if file.content_type == 'application/pdf' and file.size < 100000:
        with tempfile.TemporaryFile() as fp:
            fp.write(file.read())
            text = extract_text_from_pdf(fp)
        if text:
            text = text.replace("\n", "").split("Коронавирусы подобные SARS-CoVВККоронавирус SARS-CoV-2")
        to_return = []
        if text:
            for i in text:
                k = i.split("N")
                if len(k) > 1 and k[1].split(" ")[0].isdigit():
                    result = json.dumps({"pk": k[1].split(" ")[0], "result": [{"dnk_SARS": "Положительно" if "+" in i else "Отрицательно"}]})
                    to_return.append({"pk": k[1].split(" ")[0], "result": "Положительно" if "+" in i else "Отрицательно"})
                    http_func({"key": key_dnk, "result": result}, request.user)

    return to_return


def http_func(data, user):
    http_obj = HttpRequest()
    http_obj.POST.update(data)
    http_obj.user = user
    endpoint(http_obj)


def parse_medical_examination(request):
    result = []
    employee_data = []
    company_inn = request.POST['companyInn']
    company_file = request.FILES['file']
    wb = load_workbook(filename=company_file)
    ws = wb.active
    counter_row = 0
    for row in ws.values:
        if counter_row >= 3:
            params = {"enp": "", "snils": row[1].replace('-', '').replace(' ', ''), "check_mode": "l2-snils"}
            request_obj = HttpRequest()
            request_obj._body = params
            request_obj.user = request.user
            request_obj.method = 'POST'
            request_obj.META["HTTP_AUTHORIZATION"] = f'Bearer {Application.objects.first().key}'
            employee = check_enp(request_obj)
            employee_card = patients_search_card()
            print(employee.data)
            # harmful_factor_template = HarmfulFactor.objects.filter(title=row[7]).first().template_id

        counter_row += 1
    return result


def load_file(request):
    if request.POST['companyInn']:
        result = parse_medical_examination(request)
        return JsonResponse({"ok": True, "results": result})
    else:
        results = dnk_covid(request)
        return JsonResponse({"ok": True, "results": results})
