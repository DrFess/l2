from django.contrib import admin
from .models import IstochnikiFinansirovaniya, Napravleniya, TubesRegistration, Issledovaniya

admin.site.register(IstochnikiFinansirovaniya)  # Активация формы добавления и изменения источников финансировнаия
admin.site.register(Napravleniya)
admin.site.register(TubesRegistration)
admin.site.register(Issledovaniya)
