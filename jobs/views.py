from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Job, Application
from .forms import JobForm, JobSearchForm

# Create your views here.

class JobListView(ListView):
    model = Job
    template_name = 'job_list.html'
    context_object_name = 'all_jobs'

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter_form = JobSearchForm(self.request.GET)
        if not self.filter_form.is_valid():
            return queryset

        filters = self.filter_form.cleaned_data
        if filters['q']:
            queryset = queryset.filter(
                Q(title__icontains=filters['q'])
                | Q(company_name__icontains=filters['q'])
                | Q(description__icontains=filters['q'])
            )
        if filters['location']:
            queryset = queryset.filter(location__icontains=filters['location'])
        if filters['min_salary'] is not None:
            queryset = queryset.filter(salary__gte=filters['min_salary'])
        if filters['max_salary'] is not None:
            queryset = queryset.filter(salary__lte=filters['max_salary'])
        if filters['posted_after']:
            queryset = queryset.filter(date_posted__gte=filters['posted_after'])
        if filters['posted_before']:
            queryset = queryset.filter(date_posted__lte=filters['posted_before'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = getattr(self, 'filter_form', JobSearchForm())
        return context


class EmployerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return self.request.user.role == 'employer'

class JobDetailView(DetailView):
    model = Job
    template_name = 'job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['has_applied'] = Application.objects.filter(job=self.object, applicant=self.request.user).exists()
        
        return context

class JobCreateView(EmployerRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('job')

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        return super().form_valid(form)


class JobUpdateView(EmployerRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('job')

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


class JobDeleteView(EmployerRequiredMixin, DeleteView):
    model = Job
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('my_jobs')

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


class MyJobsListView(EmployerRequiredMixin, ListView):
    model = Job
    template_name = 'jobs/my_jobs.html'
    context_object_name = 'jobs'

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


class MyApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'jobs/my_applications.html'
    context_object_name = 'applications'

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).select_related('job')


@login_required
@require_POST
def apply_to_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    Application.objects.get_or_create(job=job, applicant=request.user)
    return redirect(reverse('job_detail', kwargs={'pk': job.pk}))
    