from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class DateInput(forms.DateInput):
    template_name = "solver/widgets/date.html"


class TextInput(forms.TextInput):
    template_name = "solver/widgets/text.html"


class ParticipantForm(forms.Form):
    name = forms.CharField(widget=TextInput(attrs={"placeholder": "Neuer Teilnehmer"}))

    def __init__(self, *args, **kwargs):
        self.participants = kwargs.pop("participants", set())
        super().__init__(*args, **kwargs)

    def clean_name(self):
        value = self.cleaned_data["name"]
        if value in self.participants:
            raise ValidationError(
                _("%(value)s is already a participant"),
                code="invalid",
                params={"value": value},
            )
        return value


class DateForm(forms.Form):
    date = forms.DateField()


class PreferenceForm(forms.Form):
    name = forms.CharField()
    date = forms.DateField()


class ScheduleCreateForm(forms.Form):
    start = forms.DateField(widget=DateInput)
    end = forms.DateField(widget=DateInput)
    exclude_weekends = forms.BooleanField(required=False)
