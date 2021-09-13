from django.urls import path
from . import views

urlpatterns = [
    path('generate', views.directions_generate),
    path('rmis-directions', views.directions_rmis_directions),
    path('rmis-direction', views.directions_rmis_direction),
    path('history', views.directions_history),
    path('result-patient-year', views.directions_result_year),
    path('result-patient-by-direction', views.results_by_direction),
    path('hosp_set_parent', views.hosp_set_parent),
    path('update_parent', views.update_parent),
    path('cancel', views.directions_cancel),
    path('results', views.directions_results),
    path('services', views.directions_services),
    path('mark-visit', views.directions_mark_visit),
    path('receive-material', views.directions_receive_material),
    path('visit-journal', views.directions_visit_journal),
    path('recv-journal', views.directions_recv_journal),
    path('last-result', views.directions_last_result),
    path('results-report', views.directions_results_report),
    path('paraclinic_form', views.directions_paraclinic_form),
    path('paraclinic_result', views.directions_paraclinic_result),
    path('anesthesia_result', views.directions_anesthesia_result),
    path('anesthesia_load', views.directions_anesthesia_load),
    path('paraclinic_result_confirm', views.directions_paraclinic_confirm),
    path('paraclinic_result_confirm_reset', views.directions_paraclinic_confirm_reset),
    path('paraclinic_result_history', views.directions_paraclinic_history),
    path('patient-history', views.directions_patient_history),
    path('data-by-fields', views.directions_data_by_fields),
    path('last-fraction-result', views.last_fraction_result),
    path('last-field-result', views.last_field_result),
    path('send-amd', views.send_amd),
    path('reset-amd', views.reset_amd),
    path('purposes', views.purposes),
    path('external-organizations', views.external_organizations),
    path('direction-in-favorites', views.direction_in_favorites),
    path('all-directions-in-favorites', views.all_directions_in_favorites),
    path('directions-type-date', views.directions_type_date),
    path('change-owner-direction', views.change_owner_direction),
    path('tubes-for-get', views.tubes_for_get),
    path('tubes-register-get', views.tubes_register_get),
    path('tubes-for-confirm', views.tubes_for_confirm),
    path('tubes-get-history', views.tubes_get_history),
    path('gen-number', views.gen_number),
    path('free-number', views.free_number),
    path('eds/required-signatures', views.eds_required_signatures),
    path('eds/documents', views.eds_documents),
]
