from django.urls import path

from . import views

urlpatterns = [
    path('create-billing', views.create_billing),
    path('update-billing', views.update_billing),
    path('confirm-billing', views.confirm_billing),
    path('get_data_for_confirmed_billing', views.get_data_for_confirmed_billing),
    path('get-research-for-billing', views.get_research_for_billing),
    path('get-billings', views.get_billings),
    path('get-billing', views.get_billing),
]
