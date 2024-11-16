import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from laboratory.decorators import group_required
from employees.models import Department, EmployeeWorkingHoursSchedule


@login_required()
@group_required('График рабочего времени')
def get_departments(request):
    departments = Department.get_active()
    return JsonResponse({"result": departments})


@login_required()
@group_required('График рабочего времени')
def get_work_time(request):
    request_data = json.loads(request.body)
    result = EmployeeWorkingHoursSchedule.get_work_time(request_data["year"], request_data["month"], request_data["departmentId"])
    return JsonResponse({"result": result})


@login_required()
@group_required('График рабочего времени')
def update_time(request):
    request_data = json.loads(request.body)
    print(request_data)
    result = {"ok": True, "message": ""}
    return JsonResponse(result)
