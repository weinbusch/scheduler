import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class DateInput(forms.DateInput):
    template_name = "solver/widgets/date.html"


class TextInput(forms.TextInput):
    template_name = "solver/widgets/text.html"


class ParticipantForm(forms.Form):
    name = forms.CharField(widget=TextInput(attrs={"placeholder": "Neuer Teilnehmer"}))
    weekdays = forms.MultipleChoiceField(
        choices=[
            (0, "montags"),
            (1, "dienstags"),
            (2, "mittwochs"),
            (3, "donnerstags"),
            (4, "freitags"),
            (5, "samstags"),
            (6, "sonntags"),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

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

    def clean_weekdays(self):
        """normalize weekday to int"""
        value = self.cleaned_data["weekdays"]
        value = [int(x) for x in value]
        return value


class DateForm(forms.Form):
    date = forms.DateField()


class PreferenceForm(forms.Form):
    name = forms.CharField()
    date = forms.DateField()


class ScheduleCreateForm(forms.Form):
    start = forms.DateField(widget=DateInput, required=True)
    end = forms.DateField(widget=DateInput, required=True)
    exclude_weekends = forms.BooleanField(required=False)

    def clean_end(self):
        start = self.cleaned_data["start"]
        end = self.cleaned_data["end"]
        if (end - start) > datetime.timedelta(days=365):
            raise ValidationError(
                _("The date range is limited to one year (365 days)"),
                code="invalid",
            )
        return end


class ScheduleSettingsForm(forms.Form):
    window = forms.IntegerField(
        widget=TextInput,
        label="Aufeinanderfolgende Tage",
        help_text=(
            "Um zu festzulegen, dass ein Teilnehmer nicht an aufeinanderfolgenden Tagen"
            " für einen Dienst eingeteilt wird, "
            "trage hier die Anzahl an aufeinanderfolgenden Tagen ein, "
            "an denen ein Teilnehmer maximal einen Dienst haben darf."
        ),
    )
