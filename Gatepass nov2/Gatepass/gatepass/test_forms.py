
from django.test import TestCase
from .forms import StudentRegistrationForm, WardenRegistrationForm, SecurityRegistrationForm

class RegistrationFormTest(TestCase):

    def test_student_registration_form_password_validation(self):
        # Test with a weak password
        form_data = {
            'hall_ticket_no': '22BH1A66A3',
            'student_name': 'Test Student',
            'room_no': '101',
            'parent_name': 'Test Parent',
            'parent_mobile': '1234567890',
            'password': 'password',
            'password2': 'password',
        }
        form = StudentRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

        # Test with a strong password
        form_data['password'] = 'Password123'
        form_data['password2'] = 'Password123'
        form = StudentRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_warden_registration_form_password_validation(self):
        # Test with a weak password
        form_data = {
            'username': 'testwarden',
            'email': 'warden@example.com',
            'password': 'password',
            'password2': 'password',
            'first_name': 'Test',
            'last_name': 'Warden',
        }
        form = WardenRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

        # Test with a strong password
        form_data['password'] = 'Password123'
        form_data['password2'] = 'Password123'
        form = WardenRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_security_registration_form_password_validation(self):
        # Test with a weak password
        form_data = {
            'username': 'testsecurity',
            'email': 'security@example.com',
            'password': 'password',
            'password2': 'password',
            'first_name': 'Test',
            'last_name': 'Security',
            'shift': 'Morning',
        }
        form = SecurityRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

        # Test with a strong password
        form_data['password'] = 'Password123'
        form_data['password2'] = 'Password123'
        form = SecurityRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
