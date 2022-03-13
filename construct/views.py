import simplejson as json
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

import directory.models as directory
from appconf.manager import SettingManager
from laboratory.decorators import group_required
from podrazdeleniya.models import Podrazdeleniya


@ensure_csrf_cookie
@login_required
def menu(request):
    return redirect('/ui/construct/menu')


@login_required
@group_required("Оператор", "Конструктор: Лабораторные исследования")
@ensure_csrf_cookie
def researches(request):
    """Конструктор исследований"""
    labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY)
    return render(request, 'construct_researches.html', {"labs": labs, "variants": directory.ResultVariants.objects.all()})


@login_required
@group_required("Оператор", "Конструктор: Лабораторные исследования")
@ensure_csrf_cookie
def researches_tune(request):
    """Настройка исследований"""
    pk = request.GET["pk"]
    return render(request, 'construct_researches_tune.html', {"pk": pk, "material_types": directory.MaterialVariants.objects.all()})


@login_required
@group_required("Оператор", "Конструктор: Лабораторные исследования")
@ensure_csrf_cookie
def researches_tune_ng(request):
    """Настройка исследований"""
    pk = request.GET["pk"]
    return render(request, 'construct_researches_tune_ng.html', {"pk": pk})


@login_required
@group_required("Оператор", "Конструктор: Ёмкости для биоматериала")
@ensure_csrf_cookie
def tubes(request):
    """Создание и редактирование ёмкостей"""
    return render(request, 'construct_tubes.html')


@login_required
@group_required("Оператор", "Конструктор: Группировка исследований по направлениям")
@ensure_csrf_cookie
def directions_group(request):
    """Группировка по направлениям"""
    labs = Podrazdeleniya.objects.filter(Q(p_type=Podrazdeleniya.LABORATORY) | Q(p_type=Podrazdeleniya.PARACLINIC))
    return render(request, 'construct_directions_group.html', {"labs": labs})


@login_required
@group_required("Оператор", "Конструктор: Настройка УЕТов")
@ensure_csrf_cookie
def uets(request):
    """Настройка УЕТов"""
    labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY)
    return render(request, 'uets.html', {"labs": labs})


@csrf_exempt
@login_required
@group_required("Оператор", "Группировка исследований по направлениям")
@ensure_csrf_cookie
def onlywith(request):
    """Настройка назначения анализов вместе"""
    if request.method == "GET":
        labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY)
        return render(request, 'onlywith.html', {"labs": labs})
    elif request.method == "POST":
        pk = int(request.POST["pk"])
        onlywith_value = int(request.POST.get("onlywith", "-1"))
        res = directory.Researches.objects.get(pk=pk)
        if onlywith_value > -1:
            res.onlywith = directory.Researches.objects.get(pk=onlywith_value)
            res.save()
        else:
            res.onlywith = None
            res.save()
        return JsonResponse({"ok": True})


@csrf_exempt
@login_required
def refs(request):
    """Настройка назначения анализов вместе"""
    if request.method == "GET":
        rows = []
        fraction = directory.Fractions.objects.get(pk=int(request.GET["pk"]))
        for r in directory.References.objects.filter(fraction=fraction).order_by("pk"):
            rows.append(
                {
                    'pk': r.pk,
                    'title': r.title,
                    'about': r.about,
                    'ref_m': json.loads(r.ref_m) if isinstance(r.ref_m, str) else r.ref_m,
                    'ref_f': json.loads(r.ref_f) if isinstance(r.ref_f, str) else r.ref_f,
                    'del': False,
                    'hide': False,
                    'isdefault': r.pk == fraction.default_ref_id,
                }
            )
        return JsonResponse(rows, safe=False)
    elif request.method == "POST":
        pk = int(request.POST["pk"])
        default = int(request.POST["default"])
        if pk > -1:
            fraction = directory.Fractions.objects.get(pk=pk)
            for r in json.loads(request.POST["refs"]):
                r["ref_m"].pop("", None)
                r["ref_f"].pop("", None)
                if r["del"] and r["pk"] != -1:
                    directory.References.objects.filter(pk=r["pk"]).delete()
                    if r["pk"] == default:
                        default = -1
                elif not r["del"] and r["pk"] == -1:
                    nrf = directory.References(title=r["title"], about=r["about"], ref_m=r["ref_m"], ref_f=r["ref_f"], fraction=fraction)
                    nrf.save()
                    if r["isdefault"]:
                        default = nrf.pk
                else:
                    row = directory.References.objects.get(pk=r["pk"])
                    row.title = r["title"]
                    row.about = r["about"]
                    row.ref_m = json.dumps(r["ref_m"])
                    row.ref_f = json.dumps(r["ref_f"])
                    row.save()
            fraction.default_ref = None if default == -1 else directory.References.objects.get(pk=default)
            fraction.save()
        return JsonResponse({"ok": True})


@login_required
@group_required("Оператор", "Конструктор: Параклинические (описательные) исследования")
@ensure_csrf_cookie
def researches_paraclinic(request):
    if SettingManager.get("paraclinic_module", default='false', default_type='b'):
        return render(request, 'construct_paraclinic.html')
    else:
        return redirect('/')


@login_required
@group_required("Оператор", "Конструктор: консультации")
@ensure_csrf_cookie
def construct_consults(request):
    if SettingManager.get("consults_module", default='false', default_type='b'):
        return render(request, 'construct_consults.html')
    else:
        return redirect('/')


@login_required
@group_required("Оператор", "Конструктор: Настройка шаблонов")
@ensure_csrf_cookie
def construct_templates(request):
    return render(request, 'construct_templates.html')


@login_required
@group_required("Оператор", "Конструктор: Настройка микробиологии")
@ensure_csrf_cookie
def construct_bacteria(request):
    return render(request, 'construct_bacteria.html')


@login_required
@group_required("Конструктор: Д-учет")
@ensure_csrf_cookie
def construct_dispensary_plan(request):
    return render(request, 'construct_dplan.html')
