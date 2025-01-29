from django.core.management.base import BaseCommand
from directory.models import Researches, ParaclinicInputGroups, ParaclinicInputField
import json
from appconf.manager import SettingManager


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('research_pk', type=int)

    def handle(self, *args, **kwargs):
        research_pk = kwargs["research_pk"]
        research_data = {}
        r = Researches.objects.get(pk=research_pk)
        research_data['title'] = r.title
        research_data['code'] = r.code
        research_data['short_title'] = r.short_title
        groups = ParaclinicInputGroups.objects.filter(research=r)
        groups_to_save = []
        for group in groups:
            fields_in_group = []
            for f in ParaclinicInputField.objects.filter(group=group, hide=False):
                field_data = {
                    'title': f.title,
                    'short_title': f.short_title,
                    'order': f.order,
                    'default_value': f.default_value,
                    'lines': f.lines,
                    'field_type': f.field_type,
                    'for_extract_card': f.for_extract_card,
                    'for_talon': f.for_talon,
                    'operator_enter_param': f.operator_enter_param,
                    'is_diag_table': f.is_diag_table,
                    'for_med_certificate': f.for_med_certificate,
                    'visibility': f.visibility,
                    'not_edit': f.not_edit,
                    'can_edit': f.can_edit_computed,
                    'controlParam': f.control_param,
                    'helper': f.helper,
                    'sign_organization': f.sign_organization,
                    'input_templates': f.input_templates,
                    'patientControlParam': f.patient_control_param_id,
                    'cdaOption': f.cda_option_id,
                    'attached': f.attached,
                    'required': f.required,
                    'hide': f.hide,
                }
                fields_in_group.append(field_data)
            groups_to_save.append(
                {
                    'title': group.title,
                    'show_title': group.show_title,
                    'order': group.order,
                    'hide': group.hide,
                    'fields': fields_in_group,
                    'fieldsInline': group.fields_inline,
                    'cdaOption': group.cda_option_id,
                    'visibility': group.visibility,
                    'display_hidden': False,
                }
            )
        research_data['paraclinic_input_groups'] = groups_to_save
        dir_tmp = SettingManager.get("dir_param")
        with open(f'{dir_tmp}/{research_pk}.json', 'w') as fp:
            json.dump(research_data, fp)
