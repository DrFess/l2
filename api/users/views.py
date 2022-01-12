from django.contrib.auth.decorators import login_required
import simplejson as json
import re

from django.contrib.auth import authenticate, login

from utils.response import status_response
import slog.models as slog
from users.models import DoctorProfile


def auth(request):
    data = json.loads(request.body)
    username = data.get('username', '')
    password = data.get('password', '')
    user = authenticate(username=username, password=password)
    f1 = re.findall(r"^([ X0-9]{5})([0-9a-fA-F]{5})$", username)
    if user:
        if user.is_active:
            login(request, user)
            log = slog.Log(key="", type=18, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=request.user.doctorprofile)
            log.save()
            return status_response(True, data={'fio': user.doctorprofile.get_full_fio()})

        return status_response(False, message="Ваш аккаунт отключен")
    elif len(password) == 0 and len(f1) == 1 and len(f1[0]) == 2:
        did = int(f1[0][0].replace("X", ""))
        u = DoctorProfile.objects.filter(pk=did).first()
        if u and u.get_login_id() == username and u.user.is_active:
            user = u.user
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            slog.Log(key='По штрих-коду', type=18, body="IP: {0}".format(slog.Log.get_client_ip(request)), user=request.user.doctorprofile).save()
            return status_response(True, data={'fio': user.doctorprofile.get_full_fio()})

    return status_response(False, message="Неверное имя пользователя или пароль")


@login_required
def change_password(request):
    doc: DoctorProfile = request.user.doctorprofile
    doc.reset_password()
    return status_response(True)
