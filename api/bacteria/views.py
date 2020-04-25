from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from directory.models import Culture, GroupCulture, Antibiotic, GroupAntibiotic


@login_required
def load_culture(request):
    type = request.GET.get('type')
    searchObj = request.GET.get('searchObj')
    groups = [{"pk": -2, "title": "не найдено"}]
    elements = []
    if searchObj == 'Бактерии':
        elements = Culture.get_cultures(type)
        groups = GroupCulture.get_all_cultures_groups()
        groups.insert(0, {"pk": -1, "title": "Все"})
        groups.insert(1, {"pk": -2, "title": "Без группы"})

    if searchObj == 'Антибиотики':
        elements = Antibiotic.get_antibiotics(type)

        groups = GroupAntibiotic.get_all_antibiotic_groups()
        groups.insert(0, {"pk": -1, "title": "Все"})
        groups.insert(1, {"pk": -2, "title": "Без группы"})
    print(elements)
    print(groups)

    return JsonResponse({"groups": groups, "elements": elements})


@login_required
def save_culture(request):
    type = request.GET.get('type')
    searchObj = request.GET.get('searchObj')
