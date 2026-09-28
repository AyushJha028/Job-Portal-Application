from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Application, Job


class JobViewTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.employer = user_model.objects.create_user(username='employer', password='test-pass-123', role='employer')
		self.seeker = user_model.objects.create_user(username='seeker', password='test-pass-123', role='seeker')
		self.job = Job.objects.create(
			title='Developer',
			company_name='Example Co',
			description='Build software',
			location='Remote',
			salary='80000.00',
			posted_by=self.employer,
		)

	def test_applying_requires_login(self):
		response = self.client.post(reverse('job_apply', args=[self.job.pk]))

		self.assertEqual(response.status_code, 302)
		self.assertIn('/accounts/login/', response.url)
		self.assertFalse(Application.objects.exists())

	def test_authenticated_user_can_apply_only_once(self):
		self.client.force_login(self.seeker)
		apply_url = reverse('job_apply', args=[self.job.pk])

		self.client.post(apply_url)
		self.client.post(apply_url)

		self.assertEqual(Application.objects.filter(job=self.job, applicant=self.seeker).count(), 1)

	def test_job_update_is_limited_to_owner(self):
		self.client.force_login(self.seeker)

		response = self.client.get(reverse('job_update', args=[self.job.pk]))

		self.assertEqual(response.status_code, 403)

	def test_job_seeker_cannot_create_a_job(self):
		self.client.force_login(self.seeker)

		response = self.client.get(reverse('job_create'))

		self.assertEqual(response.status_code, 403)

	def test_job_create_sets_current_user_as_poster(self):
		self.client.force_login(self.employer)

		response = self.client.post(reverse('job_create'), {
			'title': 'Designer',
			'company_name': 'Another Co',
			'description': 'Design interfaces',
			'location': 'Remote',
			'salary': '75000.00',
		})

		self.assertEqual(response.status_code, 302)
		created_job = Job.objects.get(title='Designer')
		self.assertEqual(created_job.posted_by, self.employer)

	def test_job_list_filters_by_keyword_location_and_salary(self):
		Job.objects.create(
			title='Designer',
			company_name='Another Co',
			description='Design interfaces',
			location='New York',
			salary='50000.00',
			posted_by=self.employer,
		)

		response = self.client.get(reverse('job'), {
			'q': 'developer',
			'location': 'remote',
			'min_salary': '70000',
		})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(list(response.context['all_jobs']), [self.job])

	def test_job_list_filters_by_posted_date(self):
		response = self.client.get(reverse('job'), {
			'posted_after': self.job.date_posted.isoformat(),
			'posted_before': self.job.date_posted.isoformat(),
		})

		self.assertEqual(list(response.context['all_jobs']), [self.job])

	def test_personal_lists_only_show_the_current_users_records(self):
		other_employer = get_user_model().objects.create_user(
			username='other-employer', password='test-pass-123', role='employer'
		)
		other_job = Job.objects.create(
			title='Analyst',
			company_name='Other Co',
			description='Analyze data',
			location='Remote',
			salary='65000.00',
			posted_by=other_employer,
		)
		Application.objects.create(job=self.job, applicant=self.seeker)
		Application.objects.create(job=other_job, applicant=other_employer)

		self.client.force_login(self.employer)
		jobs_response = self.client.get(reverse('my_jobs'))
		self.assertEqual(list(jobs_response.context['jobs']), [self.job])

		self.client.force_login(self.seeker)
		applications_response = self.client.get(reverse('my_applications'))
		self.assertEqual(list(applications_response.context['applications']), [Application.objects.get(job=self.job)])

	def test_non_owner_employer_cannot_edit_or_delete_job(self):
		other_employer = get_user_model().objects.create_user(
			username='other-employer', password='test-pass-123', role='employer'
		)
		self.client.force_login(other_employer)

		self.assertEqual(self.client.get(reverse('job_update', args=[self.job.pk])).status_code, 404)
		self.assertEqual(self.client.get(reverse('job_delete', args=[self.job.pk])).status_code, 404)

	def test_signup_login_and_password_visibility_render(self):
		signup_response = self.client.post(reverse('signup'), {
			'username': 'new-employer',
			'email': 'employer@example.com',
			'role': 'employer',
			'password1': 'StrongPass-914!',
			'password2': 'StrongPass-914!',
		})
		self.assertRedirects(signup_response, reverse('login'))
		new_user = get_user_model().objects.get(username='new-employer')
		self.assertEqual(new_user.role, 'employer')

		login_response = self.client.get(reverse('login'))
		self.assertContains(login_response, 'id="show-password"')
		self.assertContains(login_response, "passwordInput.type = showPassword.checked ? 'text' : 'password'")
		self.assertTrue(self.client.login(username='new-employer', password='StrongPass-914!'))

	def test_job_owner_can_update_and_delete_job(self):
		self.client.force_login(self.employer)
		update_response = self.client.post(reverse('job_update', args=[self.job.pk]), {
			'title': 'Senior Developer',
			'company_name': self.job.company_name,
			'description': self.job.description,
			'location': self.job.location,
			'salary': '90000.00',
		})
		self.assertRedirects(update_response, reverse('job'))
		self.job.refresh_from_db()
		self.assertEqual(self.job.title, 'Senior Developer')

		delete_response = self.client.post(reverse('job_delete', args=[self.job.pk]))
		self.assertRedirects(delete_response, reverse('my_jobs'))
		self.assertFalse(Job.objects.filter(pk=self.job.pk).exists())

	def test_complete_employer_to_seeker_workflow(self):
		self.client.force_login(self.employer)
		created_response = self.client.post(reverse('job_create'), {
			'title': 'Workflow Engineer',
			'company_name': 'Workflow Co',
			'description': 'Build a reliable workflow',
			'location': 'Remote',
			'salary': '82000.00',
		})
		self.assertRedirects(created_response, reverse('job'))
		job = Job.objects.get(title='Workflow Engineer')
		self.assertEqual(job.posted_by, self.employer)
		self.assertContains(self.client.get(reverse('my_jobs')), job.title)
		self.assertContains(self.client.get(reverse('job_detail', args=[job.pk])), 'Edit job')

		self.client.logout()
		self.client.force_login(self.seeker)
		self.assertNotContains(self.client.get(reverse('job')), 'Post a job')
		self.assertEqual(self.client.get(reverse('job_create')).status_code, 403)
		self.assertContains(self.client.get(reverse('job_detail', args=[job.pk])), 'Apply for this role')
		apply_response = self.client.post(reverse('job_apply', args=[job.pk]))
		self.assertRedirects(apply_response, reverse('job_detail', args=[job.pk]))
		self.assertContains(self.client.get(reverse('my_applications')), job.title)
		self.assertEqual(Application.objects.filter(job=job, applicant=self.seeker).count(), 1)

		self.client.logout()
		self.client.force_login(self.employer)
		self.client.post(reverse('job_delete', args=[job.pk]))
		self.assertFalse(Job.objects.filter(pk=job.pk).exists())
