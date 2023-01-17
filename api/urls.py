from django.urls import path, include

from . import views

urlpatterns = [
    path('send', views.send),
    path('endpoint', views.endpoint),
    path('departments', views.departments),
    path('otds', views.otds),
    path('laboratory-journal-params', views.laboratory_journal_params),
    path('bases', views.bases),
    path('laborants', views.laborants),
    path('current-user-info', views.current_user_info),
    path('menu', views.get_menu),
    path('directive-from', views.directive_from),
    path('load-users-by-group', views.load_docprofile_by_group),
    path('users', views.users_view),
    path('user', views.user_view),
    path('user-save', views.user_save_view),
    path('user-location', views.user_location),
    path('user-get-reserve', views.user_get_reserve),
    path('user-fill-slot', views.user_fill_slot),
    path('statistics-tickets/types', views.statistics_tickets_types),
    path('statistics-tickets/send', views.statistics_tickets_send),
    path('statistics-tickets/get', views.statistics_tickets_get),
    path('statistics-tickets/invalidate', views.statistics_tickets_invalidate),
    path('mkb10', views.mkb10),
    path('mkb10-dict', views.mkb10_dict),
    path('companies-find', views.companies_find),
    path('company-departments-find', views.company_departments_find),
    path('search-dicom', views.search_dicom),
    path('doctorprofile-search', views.doctorprofile_search),
    path('methods-of-taking', views.methods_of_taking),
    path('key-value', views.key_value),
    path('vich_code', views.vich_code),
    path('flg', views.flg),
    path('search-template', views.search_template),
    path('load-templates', views.load_templates),
    path('get-template', views.get_template),
    path('templates/update', views.update_template),
    path('modules', views.modules_view),
    path('autocomplete', views.autocomplete),
    path('job-types', views.job_types),
    path('job-save', views.job_save),
    path('job-list', views.job_list),
    path('job-cancel', views.job_cancel),
    path('reader-status', views.reader_status),
    path('reader-status-update', views.reader_status_update),
    path('actual-districts', views.actual_districts),
    path('hospitals', views.hospitals),
    path('get-all-hospitals', views.get_hospitals),
    path('rmis-link', views.rmis_link),
    path('permanent-directory', views.get_permanent_directory),
    path('screening/get-directory', views.screening_get_directory),
    path('screening/save', views.screening_save),
    path('companies', views.companies),
    path('purposes', views.purposes),
    path('result-treatment', views.result_of_treatment),
    path('title-report-filter-stattalon-fields', views.title_report_filter_stattalon_fields),
    path('input-templates/add', views.input_templates_add),
    path('input-templates/get', views.input_templates_get),
    path('input-templates/delete', views.input_templates_delete),
    path('input-templates/suggests', views.input_templates_suggests),
    path('construct-menu-data', views.construct_menu_data),
    path('current-org', views.current_org),
    path('org-generators', views.org_generators),
    path('org-generators-add', views.org_generators_add),
    path('current-org-update', views.current_org_update),
    path('get-links', views.get_links),
    path('disabled-forms', views.get_disabled_forms),
    path('disabled-categories', views.get_disabled_categories),
    path('disabled-reports', views.get_disabled_reports),
    path('unlimit-period-statistic-groups', views.unlimit_period_statistic_groups),
    path('current-time', views.current_time),
    path('search-param', views.search_param),
    path('statistic-params-search', views.statistic_params_search),
    path('researches/', include('api.researches.urls')),
    path('patients/', include('api.patients.urls')),
    path('directions/', include('api.directions.urls')),
    path('stationar/', include('api.stationar.urls')),
    path('bacteria/', include('api.bacteria.urls')),
    path('laboratory/', include('api.laboratory.urls')),
    path('plans/', include('api.plans.urls')),
    path('doctor-call/', include('api.doctor_call.urls')),
    path('extra-notification/', include('api.extra_notification.urls')),
    path('monitorings/', include('api.monitorings.urls')),
    path('reports/', include('api.reports.urls')),
    path('list-wait/', include('api.list_wait.urls')),
    path('procedural-list/', include('api.procedure_list.urls')),
    path('parse-file/', include('api.parse_file.urls')),
    path('users/', include('api.users.urls')),
    path('schedule/', include('api.schedule.urls')),
    path('external-system/', include('api.external_system.urls')),
    path('dashboards/', include('api.dashboards.urls')),
    path('districts/', include('api.districts.urls')),
    path('dynamic-directory/', include('api.dynamic_directory.urls')),
    path('health/', include('api.health.urls')),
    path('chats/', include('api.chats.urls')),
    path('ecp/', include('api.ecp.urls')),
    path('get-prices', views.get_prices),
    path('get-price-data', views.get_price_data),
    path('update-price', views.update_price),
    path('check-price-active', views.check_price_active),
    path('get-coasts-researches-in-price', views.get_coasts_researches_in_price),
    path('update-coast-research-in-price', views.update_coast_research_in_price),
    path('add-research-in-price', views.add_research_in_price),
    path('get-research-list', views.get_research_list),
    path('delete-research-in-price', views.delete_research_in_price),
    path('get-companies', views.get_companies),
    path('get-contracts', views.get_contracts),
    path('get-company', views.get_company),
    path('update-company', views.update_company),
    path('update-department', views.update_department),
    path('add-department', views.add_department),
    path('get-harmful-factors', views.get_harmful_factors),
    path('get-template-researches-pks', views.get_template_researches_pks),
    path('get-templates', views.get_templates),
    path('update-factor', views.update_factor),
    path('add-factor', views.add_factor),
    path('get-research-sets', views.get_research_sets),
    path('get-researches-in-set', views.get_researches_in_set),
    path('add-research-in-set', views.add_research_in_set),
    path('update-order-in-set', views.update_order_in_set),
    path('add-research-set', views.add_research_set),
    path('update-research-set', views.update_research_set),
    path('hide-research-set', views.hide_research_set),
]
