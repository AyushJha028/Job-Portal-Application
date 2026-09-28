from django import forms
from .models import Job, Application


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company_name', 'description', 'location', 'salary']


class JobSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Title, company, or keyword')
    location = forms.CharField(required=False)
    min_salary = forms.DecimalField(required=False, min_value=0, label='Minimum salary')
    max_salary = forms.DecimalField(required=False, min_value=0, label='Maximum salary')
    posted_after = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    posted_before = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
        