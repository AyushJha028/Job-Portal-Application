from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.JobCreateView.as_view(), name='job_create'),
    path('my-jobs/', views.MyJobsListView.as_view(), name='my_jobs'),
    path('my-applications/', views.MyApplicationListView.as_view(), name='my_applications'),
    path('', views.JobListView.as_view(), name='job'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('<int:pk>/update/', views.JobUpdateView.as_view(), name='job_update'),
    path('<int:pk>/delete/', views.JobDeleteView.as_view(), name='job_delete'),
    path('<int:pk>/apply/', views.apply_to_job, name='job_apply'),
]