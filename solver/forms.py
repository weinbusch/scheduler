from django import forms


class DateForm(forms.Form):
    date = forms.DateField()


class PreferenceForm(forms.Form):
    name = forms.CharField()
    date = forms.DateField()


class ScheduleCreateForm(forms.Form):
    start = forms.DateField()
    end = forms.DateField()
    exclude_weekends = forms.BooleanField(required=False)
