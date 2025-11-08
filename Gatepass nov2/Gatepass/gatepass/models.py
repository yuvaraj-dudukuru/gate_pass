from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class User(AbstractUser):
    """Custom User model with role-based authentication"""
    
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('warden', 'Warden'),
        ('security', 'Security'),
        ('student', 'Student'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True, null=True, blank=True)
    mobile_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex=r'^\d{10}$', message='Mobile number must be 10 digits')],
        unique=True,
        null=True,
        blank=True
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Student(models.Model):
    """Student profile model"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    hall_ticket_no = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=100)
    room_no = models.CharField(max_length=10)
    parent_name = models.CharField(max_length=100)
    parent_mobile = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex=r'^\d{10}$', message='Parent mobile number must be 10 digits')],
        unique=True
    )
    
    def __str__(self):
        return f"{self.student_name} ({self.hall_ticket_no})"
    
    @property
    def username_format(self):
        """Generate username format: Name@last4digits"""
        last_4_digits = self.hall_ticket_no[-4:]
        return f"{self.student_name.replace(' ', '')}@{last_4_digits}"


class Warden(models.Model):
    """Warden profile model"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='warden_profile')
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} (Warden)"


class Security(models.Model):
    """Security profile model"""
    SHIFT_CHOICES = [
        ('Morning', 'Morning'),
        ('Afternoon', 'Afternoon'),
        ('Night', 'Night'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='security_profile')
    name = models.CharField(max_length=100)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='Morning')
    
    def __str__(self):
        return f"{self.name} (Security)"


class GatePass(models.Model):
    """Gate pass request model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('warden_approved', 'Warden Approved'),
        ('warden_rejected', 'Warden Rejected'),
        ('security_approved', 'Security Approved'),
        ('returned', 'Returned'),
        ('completed', 'Completed'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='gatepass_requests')
    outing_date = models.DateField()
    outing_time = models.TimeField()
    expected_return_date = models.DateField()
    expected_return_time = models.TimeField()
    purpose = models.TextField(max_length=500, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    warden_approval = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='warden_approvals',
        limit_choices_to={'role': 'warden'}
    )
    security_approval = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='security_approvals',
        limit_choices_to={'role': 'security'}
    )
    warden_rejection_reason = models.TextField(max_length=500, null=True, blank=True)
    parent_verification = models.BooleanField(default=False)
    actual_return_date = models.DateField(null=True, blank=True)
    actual_return_time = models.TimeField(null=True, blank=True)
    return_verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='return_verifications',
        limit_choices_to={'role': 'security'}
    )
    return_notes = models.TextField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"GatePass for {self.student.student_name} - {self.outing_date}"
    
    def get_appropriate_warden(self):
        """Get warden based on student's gender"""
        if self.student.user.gender == 'M':
            return User.objects.filter(role='warden', gender='M').first()
        elif self.student.user.gender == 'F':
            return User.objects.filter(role='warden', gender='F').first()
        return None


class ParentVerification(models.Model):
    """Parent verification model"""
    
    gatepass = models.OneToOneField(GatePass, on_delete=models.CASCADE, related_name='verification')
    parent_mobile = models.CharField(max_length=10)
    verification_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Parent verification for {self.gatepass.student.student_name}"


class Notification(models.Model):
    """Notification model for tracking status updates"""
    
    NOTIFICATION_TYPES = [
        ('gatepass_request', 'Gate Pass Request'),
        ('warden_approval', 'Warden Approval'),
        ('warden_rejection', 'Warden Rejection'),
        ('security_approval', 'Security Approval'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    gatepass = models.ForeignKey(GatePass, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.user.username}"