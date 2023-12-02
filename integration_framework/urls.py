from django.urls import path

from . import views

urlpatterns = [
    path('result/next', views.next_result_direction),
    path('result/amd', views.get_dir_amd),
    path('result/cpp', views.get_dir_cpp),
    path('result/n3', views.get_dir_n3),
    path('result/resend-l2', views.resend_dir_l2),
    path('result/resend-crie', views.resend_dir_crie),
    path('result/sendamd', views.result_amd_send),
    path('result/sendcpp', views.result_cpp_send),
    path('result/pdf', views.get_pdf_result),
    path('external-result/pdf', views.external_get_pdf_result),
    path('direction/pdf', views.get_pdf_direction),
    path('direction/data', views.direction_data),
    path('direction/records', views.direction_records),
    path('direction/category-confirm', views.directions_by_category_result_year),
    path('direction/result', views.results_by_direction),
    path('iss/data', views.issledovaniye_data),
    path('iss/data-simple', views.issledovaniye_data_simple),
    path('iss/data-multi', views.issledovaniye_data_multi),
    path('set-core-id', views.set_core_id),
    path('check-enp', views.check_enp),
    path('get-patient-results-covid19', views.patient_results_covid19),
    path('log', views.make_log),
    path('crie-status', views.crie_status),
    path('doc-call-create', views.external_doc_call_create),
    path('doc-call-update-status', views.external_doc_call_update_status),
    path('doc-call-send', views.external_doc_call_send),
    path('send-result', views.external_research_create),
    path('send-direction', views.external_direction_create),
    path('get-directions', views.get_directions),
    path('get-direction-data-by-period', views.get_direction_data_by_period),
    path('get-directions-data', views.get_direction_data_by_num),
    path('protocol-result', views.get_protocol_result),
    path('eds/get-user-data', views.eds_get_user_data),
    path('eds/get-cda-data', views.eds_get_cda_data),
    path('external/check-result', views.external_check_result),
    path('get-hosp-services', views.get_hosp_services),
    path('mkb10', views.mkb10),
    path('hosp-record', views.hosp_record),
    path('hosp-record-add-file', views.add_file_hospital_plan),
    path('hosp-record-list', views.hosp_record_list),
    path('check-employee', views.check_employee),
    path('schedule/hospitalization-plan-research', views.hospitalization_plan_research),
    path('schedule/available-hospitalization-plan', views.available_hospitalization_plan),
    path('schedule/check-hosp-slot-before-save', views.check_hosp_slot_before_save),
    path('documents-lk', views.documents_lk),
    path('details-document-lk', views.details_document_lk),
    path('document-lk-save', views.document_lk_save),
    path('forms-lk', views.forms_lk),
    path('pdf-forms-lk', views.pdf_form_lk),
    path('files-params', views.get_limit_download_files),
    path('plan-messages', views.get_all_messages_by_plan_id),
    path('amd-save', views.amd_save),
    path('register-emdr-id', views.register_emdr_id),
    path('get-direction-pk-by-emdr-id', views.get_direction_pk_by_emdr_id),
    path('get-value-field', views.get_value_field),
    path('get-price-data', views.get_price_data),
    path('get-prices-by-date', views.get_prices_by_date),
    path('get-reference-books', views.get_reference_books),
    path('send-laboratory-order', views.send_laboratory_order),
]
