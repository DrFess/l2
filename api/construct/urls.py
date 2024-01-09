from django.urls import path

from . import views

urlpatterns = [
    path('laboratory/get-departments', views.get_departments),
    path('laboratory/get-tubes', views.get_tubes),
    path('laboratory/update-order-research', views.update_order_research),
    path('laboratory/update-order-fraction', views.update_order_fraction),
    path('laboratory/change-visibility-research', views.change_visibility_research),
    path('laboratory/get-research', views.get_research),
    path('laboratory/update-research', views.update_research),
]
