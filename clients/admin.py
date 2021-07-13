import clients.models as models
from django.contrib import admin


@admin.register(models.Individual)
class IndividualAdmin(admin.ModelAdmin):
    list_display = (
        'family',
        'name',
        'patronymic',
        'birthday',
    )
    search_fields = ('family',)


@admin.register(models.DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Document)
class DocumentAdmin(admin.ModelAdmin):
    raw_id_fields = ('individual',)


@admin.register(models.CardBase)
class CardBaseAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Card)
class CardAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'individual',
        'polis',
        'mother',
        'father',
        'curator',
        'agent',
        'payer',
    )

    search_fields = ('individual__family',)


@admin.register(models.ScreeningRegPlan)
class ScreeningRegPlanAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'card',
    )

    search_fields = ('research__title',)


@admin.register(models.Phones)
class PhonesAdmin(admin.ModelAdmin):
    pass


@admin.register(models.AgeCache)
class AgeCacheAdmin(admin.ModelAdmin):
    pass


@admin.register(models.District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_ginekolog',
        'code_poliklinika',
    )


@admin.register(models.DispensaryReg)
class DispensaryRegAdmin(admin.ModelAdmin):
    raw_id_fields = ('card',)


@admin.register(models.BenefitType)
class BenefitTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.BenefitReg)
class BenefitRegAdmin(admin.ModelAdmin):
    raw_id_fields = ('card',)


@admin.register(models.DispensaryRegPlans)
class ResDispensaryRegPlans(admin.ModelAdmin):
    raw_id_fields = ('card',)
    list_display = (
        'card',
        'research',
        'speciality',
        'date',
    )
    list_display_links = (
        'card',
        'research',
        'speciality',
        'date',
    )
    search_fields = (
        'research__title',
        'speciality__title',
    )
