from django.forms import ModelForm, widgets
from django import forms
from django.utils.html import format_html
from itertools import chain
from django_teams.models import Team
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text

class TeamCreateForm(ModelForm):
    class Meta:
        model = Team

class TeamEditForm(ModelForm):
    """This form is very complicated;
    it consists of a hash containing :
        An array of pending requests
        An array of team leaders
        An array of team members
    The form should allow the team leaders to perform the following
    actions on any number of elements from each array, at the same time:
        Pending requests;
            approve
            deny
        Team Leaders
            Demote
            Remove
        Team Members
            Promote
            Remove
    """

    class Meta:
        model = Team
        
class LinkedCheckboxSelectMultiple (widgets.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = ['<ul>']
        # Normalize to strings
        str_values = set([force_text(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = format_html(' for="{0}"', final_attrs['id'])
            else:
                label_for = ''

            cb = widgets.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_text(option_value)
            rendered_cb = cb.render(name, option_value)
            text = option_label.split('/',3)
            if len(text) == 4 : # If we got a proper split
               obj_model = text[0]
               obj_id = text[1]
               option_label = force_text(text[3] + " by " + text[2]) # Project Name by Student
               output.append(format_html('<li><label{0}>{1} <a href="/' + obj_model + 's/' + obj_id + '/">{2}</a></label></li>',
                                         label_for, rendered_cb, option_label))
            else: # Default to normal behavior without proper split
               option_label = force_text(option_label)
               output.append(format_html('<li><label{0}>{1} {2}</label></li>',
                                         label_for, rendered_cb, option_label))
        output.append('</ul>')
        return mark_safe('\n'.join(output))

def action_formset(qset, actions, link=False):
    """A form factory which returns a form which allows the user to pick a specific action to
    perform on a chosen subset of items from a queryset.
    """
    class _ActionForm(forms.Form):
        if(link):
           items = forms.ModelMultipleChoiceField(queryset = qset, required=False, widget=LinkedCheckboxSelectMultiple)
        else: 
           items = forms.ModelMultipleChoiceField(queryset = qset, required=False, widget=widgets.CheckboxSelectMultiple)
        action = forms.ChoiceField(choices = zip(actions, actions), required=False)

    return _ActionForm
