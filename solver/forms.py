from django import forms


class DateInput(forms.DateInput):
    template_name = "solver/widgets/date.html"


class DateForm(forms.Form):
    date = forms.DateField()


class PreferenceForm(forms.Form):
    name = forms.CharField()
    date = forms.DateField()


class ScheduleCreateForm(forms.Form):
    start = forms.DateField(widget=DateInput)
    end = forms.DateField(widget=DateInput)
    exclude_weekends = forms.BooleanField(required=False)
