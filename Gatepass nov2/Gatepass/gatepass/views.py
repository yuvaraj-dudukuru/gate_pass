from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.views import LoginView
import random
import string
from datetime import datetime, date, time
from .models import User, Student, Warden, Security, GatePass, ParentVerification, Notification
from .forms import (
    StudentRegistrationForm, WardenRegistrationForm, SecurityRegistrationForm,
    GatePassRequestForm, WardenApprovalForm, ParentVerificationForm, SecurityReturnForm, WardenDateFilterForm
)


def home(request):
    """Home page"""
    return render(request, 'gatepass/home.html')


class CustomLoginView(LoginView):
    """Custom login view with role-based redirect"""
    template_name = 'gatepass/login.html'
    extra_context = None
    ROLE_TITLES = {
        'student': 'Student Login',
        'warden': 'Warden Login',
        'security': 'Security Login',
        'superadmin': 'Admin Login',
    }
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard_redirect')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = self.request.GET.get('role')
        context['role'] = role
        context['role_title'] = self.ROLE_TITLES.get(role, 'Login')
        # Provide registration forms for the Register tab
        context['active_role'] = role or 'student'
        context['student_form'] = StudentRegistrationForm()
        context['warden_form'] = WardenRegistrationForm()
        context['security_form'] = SecurityRegistrationForm()
        return context

    def form_valid(self, form):
        """Allow login only for approved users; show friendly error otherwise."""
        user = form.get_user()
        if hasattr(user, 'is_approved') and not user.is_approved:
            messages.error(self.request, 'Your account is awaiting approval. Please try again later.')
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirect users to their appropriate dashboard based on role"""
        user = self.request.user
        if user.is_authenticated:
            if user.role == 'student':
                return '/student/dashboard/'
            elif user.role == 'warden':
                return '/warden/dashboard/'
            elif user.role == 'security':
                return '/security/dashboard/'
            elif user.role == 'superadmin':
                return '/superadmin/dashboard/'
        return '/'


@login_required
def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard"""
    user = request.user
    if user.role == 'student':
        return redirect('student_dashboard')
    elif user.role == 'warden':
        return redirect('warden_dashboard')
    elif user.role == 'security':
        return redirect('security_dashboard')
    elif user.role == 'superadmin':
        return redirect('superadmin_dashboard')
    else:
        return redirect('home')


def custom_logout(request):
    """Custom logout view that handles both GET and POST requests"""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
    return redirect('home')


def logout_confirm(request):
    """Logout confirmation page"""
    if not request.user.is_authenticated:
        return redirect('home')
    return render(request, 'gatepass/logout_confirm.html')


def register_router(request):
    """Backwards-compatible entry; redirected to unified register with default role."""
    role = request.GET.get('role') or 'student'
    return redirect(f"/register/?role={role}")


def register(request):
    """Unified registration view that renders role-specific forms in one place."""
    role = request.GET.get('role') if request.method == 'GET' else request.POST.get('role')
    if role not in ['student', 'warden', 'security']:
        role = 'student'

    context = { 'active_role': role }

    if request.method == 'POST':
        if role == 'student':
            form = StudentRegistrationForm(request.POST)
            if form.is_valid():
                from django.db import IntegrityError
                try:
                    with transaction.atomic():
                        data = form.cleaned_data
                        base_username = f"{data['student_name'].replace(' ', '')}@{data['hall_ticket_no'][-4:]}"
                        username = base_username
                        # Ensure username uniqueness
                        suffix = 1
                        while User.objects.filter(username=username).exists():
                            username = f"{base_username}{suffix}"
                            suffix += 1
                        user = User.objects.create_user(
                            username=username,
                            email=(data.get('email') or None),
                            password=data['password1'],
                            role='student',
                            mobile_number=data.get('mobile_number') or None,
                            gender=data.get('gender') or None,
                            is_approved=False
                        )
                        student = form.save(commit=False)
                        student.user = user
                        student.save()
                        messages.success(request, f"Registration successful! Your username is {username}. Please wait for admin approval before logging in.")
                        return redirect('login')
                except IntegrityError as e:
                    messages.error(request, 'A user with the same details already exists. Please adjust and try again.')
                    # fall through to re-render form with errors
            context['student_form'] = form
        elif role == 'warden':
            form = WardenRegistrationForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        data = form.cleaned_data
                        user = User.objects.create_user(
                            username=data['username'],
                            email=data['email'],
                            password=data['password1'],
                            role='warden',
                            mobile_number=data.get('mobile_number') or None,
                            gender=data.get('gender') or None,
                            first_name=data['first_name'],
                            last_name=data['last_name'],
                            is_approved=False
                        )
                        Warden.objects.create(
                            user=user,
                            name=f"{data['first_name']} {data['last_name']}",
                            department=data.get('department', '')
                        )
                        messages.success(request, 'Registration successful! Please wait for admin approval.')
                        return redirect('login')
                except Exception as e:
                    # Handle rare DB edge cases (e.g., race for username/email)
                    messages.error(request, 'A user with this Username, Email, or Mobile already exists, or another unexpected error happened. Please check and try again.')
            else:
                # Show all form errors as toasts (frontend renders inline errors as well)
                for field, errors in form.errors.items():
                    label = form.fields[field].label if field in form.fields else field
                    for error in errors:
                        messages.error(request, f"{label}: {error}")
            context['warden_form'] = form
        elif role == 'security':
            form = SecurityRegistrationForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    data = form.cleaned_data
                    user = User.objects.create_user(
                        username=data['username'],
                        email=data['email'],
                        password=data['password1'],
                        role='security',
                        mobile_number=data.get('mobile_number') or None,
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                        is_approved=False
                    )
                    Security.objects.create(
                        user=user,
                        name=f"{data['first_name']} {data['last_name']}",
                        shift=data.get('shift', '')
                    )
                    messages.success(request, 'Registration successful! Please wait for admin approval.')
                    return redirect('login')
            context['security_form'] = form
    else:
        # GET - initialize all forms to support single form with role dropdown
        context['student_form'] = StudentRegistrationForm()
        context['warden_form'] = WardenRegistrationForm()
        context['security_form'] = SecurityRegistrationForm()

    # If user is authenticated, avoid showing register; go to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    # If query param tab=register is desired, we can keep using login page tabs.
    if request.method == 'GET' and request.GET.get('embed') == 'auth':
        # Optionally render inside auth tabs
        return render(request, 'gatepass/login.html', context)
    return render(request, 'gatepass/register.html', context)


def register_student(request):
    """Student registration view"""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Create user
                student_data = form.cleaned_data
                username = f"{student_data['student_name'].replace(' ', '')}@{student_data['hall_ticket_no'][-4:]}"
                
                user = User.objects.create_user(
                    username=username,
                    email=(student_data.get('email') or None),
                    password=student_data['password1'],
                    role='student',
                    mobile_number=student_data.get('mobile_number') or None,
                    gender=student_data.get('gender') or None,
                    is_approved=False
                )
                
                # Create student profile
                student = form.save(commit=False)
                student.user = user
                student.save()
                
                messages.success(request, 'Registration successful! Please wait for admin approval.')
                return redirect('login')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'gatepass/register_student.html', {'form': form})


def register_warden(request):
    """Warden registration view"""
    if request.method == 'POST':
        form = WardenRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                warden_data = form.cleaned_data
                
                user = User.objects.create_user(
                    username=warden_data['username'],
                    email=warden_data['email'],
                    password=warden_data['password1'],
                    role='warden',
                    mobile_number=warden_data.get('mobile_number') or None,
                    gender=warden_data.get('gender') or None,
                    first_name=warden_data['first_name'],
                    last_name=warden_data['last_name'],
                    is_approved=False
                )
                
                # Create warden profile
                Warden.objects.create(
                    user=user,
                    name=f"{warden_data['first_name']} {warden_data['last_name']}",
                    department=warden_data.get('department', '')
                )
                
                messages.success(request, 'Registration successful! Please wait for admin approval.')
                return redirect('login')
    else:
        form = WardenRegistrationForm()
    
    return render(request, 'gatepass/register_warden.html', {'form': form})


def register_security(request):
    """Security registration view"""
    if request.method == 'POST':
        form = SecurityRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                security_data = form.cleaned_data
                
                user = User.objects.create_user(
                    username=security_data['username'],
                    email=security_data['email'],
                    password=security_data['password1'],
                    role='security',
                    mobile_number=security_data.get('mobile_number') or None,
                    first_name=security_data['first_name'],
                    last_name=security_data['last_name'],
                    is_approved=False
                )
                
                # Create security profile
                Security.objects.create(
                    user=user,
                    name=f"{security_data['first_name']} {security_data['last_name']}",
                    shift=security_data.get('shift', '')
                )
                
                messages.success(request, 'Registration successful! Please wait for admin approval.')
                return redirect('login')
    else:
        form = SecurityRegistrationForm()
    
    return render(request, 'gatepass/register_security.html', {'form': form})


@login_required
def student_dashboard(request):
    """Student dashboard"""
    if request.user.role != 'student':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Check for overdue returns
    check_overdue_returns()
    
    student = get_object_or_404(Student, user=request.user)
    gatepasses = GatePass.objects.filter(student=student).order_by('-created_at')
    
    # Get statistics
    total_requests = gatepasses.count()
    pending_requests = gatepasses.filter(status='pending').count()
    approved_requests = gatepasses.filter(status__in=['warden_approved', 'security_approved']).count()
    rejected_requests = gatepasses.filter(status='warden_rejected').count()
    
    # Get recent notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'student': student,
        'gatepasses': gatepasses,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'notifications': notifications,
    }
    return render(request, 'gatepass/student_dashboard.html', context)


@login_required
def create_gatepass(request):
    """Create gatepass request"""
    if request.user.role != 'student':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    student = get_object_or_404(Student, user=request.user)
    
    if request.method == 'POST':
        form = GatePassRequestForm(request.POST)
        if form.is_valid():
            gatepass = form.save(commit=False)

            # Construct outing_time
            outing_hour = int(form.cleaned_data['outing_hour'])
            outing_minute = int(form.cleaned_data['outing_minute'])
            outing_ampm = form.cleaned_data['outing_ampm']
            if outing_ampm == 'PM' and outing_hour != 12:
                outing_hour += 12
            elif outing_ampm == 'AM' and outing_hour == 12:
                outing_hour = 0
            gatepass.outing_time = time(outing_hour, outing_minute)

            # Construct expected_return_time
            return_hour = int(form.cleaned_data['expected_return_hour'])
            return_minute = int(form.cleaned_data['expected_return_minute'])
            return_ampm = form.cleaned_data['expected_return_ampm']
            if return_ampm == 'PM' and return_hour != 12:
                return_hour += 12
            elif return_ampm == 'AM' and return_hour == 12:
                return_hour = 0
            gatepass.expected_return_time = time(return_hour, return_minute)
            
            gatepass.student = student
            gatepass.save()
            
            print(f"DEBUG: Student {student.student_name} (ID: {student.id}) gender: {student.user.gender}")

            # Create parent verification
            verification_code = ''.join(random.choices(string.digits, k=6))
            ParentVerification.objects.create(
                gatepass=gatepass,
                parent_mobile=student.parent_mobile,
                verification_code=verification_code
            )
            
            # Create notification for appropriate wardens based on student's gender
            wardens_to_notify = User.objects.filter(role='warden', is_approved=True, gender=student.user.gender)
            
            print(f"DEBUG: Wardens to notify (gender-matched): {list(wardens_to_notify.values_list('username', 'gender'))}")

            if wardens_to_notify.exists():
                for warden_user in wardens_to_notify:
                    Notification.objects.create(
                        user=warden_user,
                        gatepass=gatepass,
                        notification_type='gatepass_request',
                        message=f"New gatepass request from {student.student_name}"
                    )
            else:
                # Fallback: If no specific gender-matching warden found, notify all approved wardens
                all_approved_wardens = User.objects.filter(role='warden', is_approved=True)
                print(f"DEBUG: No gender-matched wardens found. Notifying all approved wardens: {list(all_approved_wardens.values_list('username', 'gender'))}")
                for warden_user in all_approved_wardens:
                    Notification.objects.create(
                        user=warden_user,
                        gatepass=gatepass,
                        notification_type='gatepass_request',
                        message=f"New gatepass request from {student.student_name} (No gender-specific warden found)"
                    )
            
            messages.success(request, 'Gatepass request submitted successfully!')
            return redirect('student_dashboard')
    else:
        form = GatePassRequestForm()
    
    return render(request, 'gatepass/create_gatepass.html', {
        'form': form,
        'student': student
    })


@login_required
def warden_dashboard(request):
    """Warden dashboard"""
    if request.user.role != 'warden':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Check for overdue returns
    check_overdue_returns()
    
    # Initialize filter form
    filter_form = WardenDateFilterForm(request.GET)
    
    # Get all gatepass requests for filtering
    all_requests = GatePass.objects.all().order_by('-created_at')
    print(f"DEBUG: Warden {request.user.username} (ID: {request.user.id}) gender: {request.user.gender}")
    print(f"DEBUG: All requests before gender filter: {list(all_requests.values_list('id', 'student__user__gender', 'status'))}")

    # Gender filter is removed to show all requests to all wardens.
    # if request.user.gender:
    #     gender_filtered = all_requests.filter(student__user__gender=request.user.gender)
    #     if gender_filtered.exists():
    #         all_requests = gender_filtered
    #         print(f"DEBUG: Requests after gender filter (matched): {list(all_requests.values_list('id', 'student__user__gender', 'status'))}")
    #     else:
    #         print(f"DEBUG: No requests found matching warden's gender ({request.user.gender}). All requests queryset is now empty.")
    #         all_requests = gender_filtered # This will be an empty queryset
    # else:
    #     print("DEBUG: Warden gender not set. No gender filter applied.")
    
    # Apply date and status filters
    if filter_form.is_valid():
        from_date = filter_form.cleaned_data.get('from_date')
        to_date = filter_form.cleaned_data.get('to_date')
        status_filter = filter_form.cleaned_data.get('status_filter')
        
        if from_date:
            all_requests = all_requests.filter(outing_date__gte=from_date)
        if to_date:
            all_requests = all_requests.filter(outing_date__lte=to_date)
        if status_filter:
            all_requests = all_requests.filter(status=status_filter)
    
    # Get pending gatepass requests
    pending_requests = all_requests.filter(status='pending')
    
    # Get approved requests (both by this warden and all approved)
    approved_requests = all_requests.filter(status='warden_approved')[:10]
    
    # Get rejected requests by this warden
    rejected_requests = all_requests.filter(
        status='warden_rejected',
        warden_approval=request.user
    )[:10]
    
    # Get returned requests (students who have returned)
    returned_requests = all_requests.filter(status='returned')[:10]
    
    # Get students currently out
    students_out_requests = all_requests.filter(status='security_approved')[:10]
    
    # Get statistics (use filtered data for consistency)
    total_pending = all_requests.filter(status='pending').count()
    total_approved = all_requests.filter(status='warden_approved').count()
    total_rejected = all_requests.filter(warden_approval=request.user, status='warden_rejected').count()
    total_returned = all_requests.filter(status='returned').count()
    students_out = all_requests.filter(status='security_approved').count()
    
    # Get filtered counts for display
    filtered_count = all_requests.count()
    
    # Get recent notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'filter_form': filter_form,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'returned_requests': returned_requests,
        'students_out_requests': students_out_requests,
        'total_pending': total_pending,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'total_returned': total_returned,
        'students_out': students_out,
        'filtered_count': filtered_count,
        'notifications': notifications,
    }
    return render(request, 'gatepass/warden_dashboard.html', context)


@login_required
def warden_approve_gatepass(request, gatepass_id):
    if request.user.role != 'warden':
        messages.error(request, 'Access denied.')
        return redirect('home')
    gatepass = get_object_or_404(GatePass, id=gatepass_id)
    # BLOCK DUPLICATE APPROVAL/REJECTION
    if gatepass.status != 'pending':
        if request.method == 'POST':
            messages.info(request, 'This gatepass has already been processed.')
            return redirect('warden_dashboard')
        return render(request, 'gatepass/warden_approve.html', {
            'gatepass': gatepass,
            'readonly': True
        })
    if request.method == 'POST':
        form = WardenApprovalForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            parent_verification = form.cleaned_data['parent_verification']
            if action == 'approve':
                if not parent_verification:
                    messages.error(request, 'Parent verification must be completed before approval.')
                    return redirect('warden_dashboard')
                gatepass.status = 'warden_approved'
                gatepass.warden_approval = request.user
                gatepass.parent_verification = True
                gatepass.save()
                security_users = User.objects.filter(role='security')
                for security in security_users:
                    Notification.objects.create(
                        user=security,
                        gatepass=gatepass,
                        notification_type='warden_approval',
                        message=f"Gatepass approved by warden for {gatepass.student.student_name}"
                    )
                Notification.objects.create(
                    user=gatepass.student.user,
                    gatepass=gatepass,
                    notification_type='warden_approval',
                    message="Your gatepass request has been approved by the warden."
                )
                messages.success(request, 'Gatepass approved successfully!')
            elif action == 'reject':
                gatepass.status = 'warden_rejected'
                gatepass.warden_approval = request.user
                gatepass.warden_rejection_reason = form.cleaned_data['rejection_reason']
                gatepass.save()
                Notification.objects.create(
                    user=gatepass.student.user,
                    gatepass=gatepass,
                    notification_type='warden_rejection',
                    message=f"Your gatepass request has been rejected. Reason: {gatepass.warden_rejection_reason}"
                )
                messages.success(request, 'Gatepass rejected.')
            return redirect('warden_dashboard')
    else:
        form = WardenApprovalForm()
    return render(request, 'gatepass/warden_approve.html', {
        'form': form,
        'gatepass': gatepass,
        'readonly': False
    })


@login_required
def security_dashboard(request):
    """Security dashboard"""
    if request.user.role != 'security':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Check for overdue returns
    check_overdue_returns()
    
    # Get approved gatepasses waiting for security approval
    approved_requests = GatePass.objects.filter(
        status='warden_approved'
    ).order_by('-created_at')
    
    # Get security approved requests (students who have left but not returned)
    security_approved = GatePass.objects.filter(
        status='security_approved',
        security_approval=request.user
    ).order_by('-created_at')[:10]
    
    # Get returned requests
    returned_requests = GatePass.objects.filter(
        status='returned',
        return_verified_by=request.user
    ).order_by('-created_at')[:10]
    
    # Get statistics
    total_pending = approved_requests.count()
    total_approved = GatePass.objects.filter(security_approval=request.user, status='security_approved').count()
    total_returned = GatePass.objects.filter(return_verified_by=request.user, status='returned').count()
    
    # Get recent notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'approved_requests': approved_requests,
        'security_approved': security_approved,
        'returned_requests': returned_requests,
        'total_pending': total_pending,
        'total_approved': total_approved,
        'total_returned': total_returned,
        'notifications': notifications,
    }
    return render(request, 'gatepass/security_dashboard.html', context)


@login_required
def security_approve_gatepass(request, gatepass_id):
    """Security approval for gatepass"""
    if request.user.role != 'security':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    gatepass = get_object_or_404(GatePass, id=gatepass_id)
    
    # Check if warden has approved first
    if gatepass.status != 'warden_approved':
        messages.error(request, 'This gatepass must be approved by warden first.')
        return redirect('security_dashboard')
    
    if request.method == 'POST':
        gatepass.status = 'security_approved'
        gatepass.security_approval = request.user
        gatepass.save()
        
        # Create notification for student
        Notification.objects.create(
            user=gatepass.student.user,
            gatepass=gatepass,
            notification_type='security_approval',
            message="Your gatepass has been approved by security. You can now leave the campus."
        )
        
        messages.success(request, 'Gatepass approved by security!')
        return redirect('security_dashboard')
    
    return render(request, 'gatepass/security_approve.html', {
        'gatepass': gatepass
    })


@login_required
def superadmin_dashboard(request):
    """Super admin dashboard"""
    if request.user.role != 'superadmin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Check for overdue returns
    check_overdue_returns()
    
    # Get pending user approvals
    pending_users = User.objects.filter(is_approved=False).exclude(role='superadmin')
    
    # Get overdue returns
    from datetime import date
    overdue_returns = GatePass.objects.filter(
        status='security_approved',
        expected_return_date__lt=date.today()
    ).order_by('expected_return_date')
    
    # Get all pending gatepass requests for superadmin approval
    pending_gatepass_approvals = GatePass.objects.filter(status='pending').order_by('-created_at')
    
    # Get statistics
    total_students = User.objects.filter(role='student').count()
    total_wardens = User.objects.filter(role='warden').count()
    total_security = User.objects.filter(role='security').count()
    total_gatepasses = GatePass.objects.count()
    pending_gatepasses = GatePass.objects.filter(status='pending').count()
    overdue_count = overdue_returns.count()
    
    # Get recent gatepass requests
    recent_gatepasses = GatePass.objects.order_by('-created_at')[:10]
    
    # Get recent notifications
    notifications = Notification.objects.order_by('-created_at')[:10]
    
    context = {
        'pending_users': pending_users,
        'overdue_returns': overdue_returns,
        'pending_gatepass_approvals': pending_gatepass_approvals,
        'total_students': total_students,
        'total_wardens': total_wardens,
        'total_security': total_security,
        'total_gatepasses': total_gatepasses,
        'pending_gatepasses': pending_gatepasses,
        'overdue_count': overdue_count,
        'recent_gatepasses': recent_gatepasses,
        'notifications': notifications,
    }
    return render(request, 'gatepass/superadmin_dashboard.html', context)


@login_required
def approve_user(request, user_id):
    """Approve user registration"""
    if request.user.role != 'superadmin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()
    
    messages.success(request, f'User {user.username} has been approved.')
    return redirect('superadmin_dashboard')


@login_required
def reject_user(request, user_id):
    """Reject user registration"""
    if request.user.role != 'superadmin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    user = get_object_or_404(User, id=user_id)
    user.delete()
    
    messages.success(request, f'User {user.username} has been rejected and deleted.')
    return redirect('superadmin_dashboard')


def parent_verification(request, gatepass_id):
    """Parent verification page"""
    gatepass = get_object_or_404(GatePass, id=gatepass_id)
    parent_verification = get_object_or_404(ParentVerification, gatepass=gatepass)
    
    if request.method == 'POST':
        form = ParentVerificationForm(request.POST, instance=parent_verification)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            if verification_code == parent_verification.verification_code:
                parent_verification.is_verified = True
                parent_verification.verified_at = timezone.now()
                parent_verification.save()
                messages.success(request, 'Parent verification completed successfully!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid verification code.')
    else:
        form = ParentVerificationForm(instance=parent_verification)
    
    return render(request, 'gatepass/parent_verification.html', {
        'form': form,
        'gatepass': gatepass,
        'parent_verification': parent_verification
    })


@login_required
def security_record_return(request, gatepass_id):
    """Security record student return"""
    if request.user.role != 'security':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    gatepass = get_object_or_404(GatePass, id=gatepass_id)
    
    # Only allow recording return for security-approved gatepasses
    if gatepass.status != 'security_approved':
        messages.error(request, 'This gatepass is not approved for outing yet.')
        return redirect('security_dashboard')
    
    if request.method == 'POST':
        form = SecurityReturnForm(request.POST, instance=gatepass)
        if form.is_valid():
            gatepass = form.save(commit=False)

            # Construct actual_return_time
            return_hour = int(form.cleaned_data['actual_return_hour'])
            return_minute = int(form.cleaned_data['actual_return_minute'])
            return_ampm = form.cleaned_data['actual_return_ampm']
            if return_ampm == 'PM' and return_hour != 12:
                return_hour += 12
            elif return_ampm == 'AM' and return_hour == 12:
                return_hour = 0
            gatepass.actual_return_time = time(return_hour, return_minute)

            gatepass.status = 'returned'
            gatepass.return_verified_by = request.user
            gatepass.save()
            
            # Create notification for student
            Notification.objects.create(
                user=gatepass.student.user,
                gatepass=gatepass,
                notification_type='return_recorded',
                message=f"Your return has been recorded on {gatepass.actual_return_date} at {gatepass.actual_return_time}"
            )
            
            messages.success(request, f'Return recorded for {gatepass.student.student_name}')
            return redirect('security_dashboard')
    else:
        form = SecurityReturnForm(instance=gatepass)
    
    return render(request, 'gatepass/security_record_return.html', {
        'form': form,
        'gatepass': gatepass
    })


def check_overdue_returns():
    """Check for overdue returns and create notifications"""
    from django.utils import timezone
    from datetime import datetime, date, time, time
    
    # Get all security approved gatepasses that haven't returned
    overdue_gatepasses = GatePass.objects.filter(
        status='security_approved',
        expected_return_date__lt=date.today()
    )
    
    for gatepass in overdue_gatepasses:
        # Check if notification already exists for today
        today = date.today()
        if not Notification.objects.filter(
            gatepass=gatepass,
            notification_type='overdue_return',
            created_at__date=today
        ).exists():
            # Create notification for warden
            if gatepass.warden_approval:
                Notification.objects.create(
                    user=gatepass.warden_approval,
                    gatepass=gatepass,
                    notification_type='overdue_return',
                    message=f"URGENT: Student {gatepass.student.student_name} has not returned after expected date {gatepass.expected_return_date}. Parent contact: {gatepass.student.parent_mobile}"
                )
            
            # Create notification for superadmin
            superadmin = User.objects.filter(role='superadmin').first()
            if superadmin:
                Notification.objects.create(
                    user=superadmin,
                    gatepass=gatepass,
                    notification_type='overdue_return',
                    message=f"URGENT: Student {gatepass.student.student_name} (Hall Ticket: {gatepass.student.hall_ticket_no}) has not returned after expected date {gatepass.expected_return_date}. Parent contact: {gatepass.student.parent_mobile}"
                )
            
            # Create notification for student
            Notification.objects.create(
                user=gatepass.student.user,
                gatepass=gatepass,
                notification_type='overdue_return',
                message=f"URGENT: You have not returned to the hostel after your expected return date {gatepass.expected_return_date}. Please contact the hostel immediately."
            )


@login_required
def superadmin_approve_gatepass(request, gatepass_id):
    """Super admin approval for gatepass"""
    if request.user.role != 'superadmin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    gatepass = get_object_or_404(GatePass, id=gatepass_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            gatepass.status = 'warden_approved'
            gatepass.warden_approval = request.user
            gatepass.save()
            
            # Create notification for security
            security_users = User.objects.filter(role='security', is_approved=True)
            for security in security_users:
                Notification.objects.create(
                    user=security,
                    gatepass=gatepass,
                    notification_type='gatepass_approved',
                    message=f"Gatepass approved by Super Admin for {gatepass.student.student_name}"
                )
            
            messages.success(request, f'Gatepass approved for {gatepass.student.student_name}')
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '')
            gatepass.status = 'warden_rejected'
            gatepass.warden_approval = request.user
            gatepass.warden_rejection_reason = reason
            gatepass.save()
            
            # Create notification for student
            Notification.objects.create(
                user=gatepass.student.user,
                gatepass=gatepass,
                notification_type='gatepass_rejected',
                message=f"Your gatepass request has been rejected by Super Admin. Reason: {reason}"
            )
            
            messages.success(request, f'Gatepass rejected for {gatepass.student.student_name}')
        
        return redirect('superadmin_dashboard')
    
    return render(request, 'gatepass/superadmin_approve_gatepass.html', {
        'gatepass': gatepass
    })


@login_required
def warden_debug(request):
    """Debug information for warden dashboard"""
    if request.user.role != 'warden':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Get all gatepass requests
    all_requests = GatePass.objects.all().order_by('-created_at')
    
    # Apply gender filter if warden has gender set
    # if request.user.gender:
    #     gender_filtered = all_requests.filter(student__user__gender=request.user.gender)
    #     if gender_filtered.exists():
    #         all_requests = gender_filtered
    
    context = {
        'warden_gender': request.user.gender,
        'all_requests': all_requests,
        'pending_requests': all_requests.filter(status='pending'),
        'approved_requests': all_requests.filter(status='warden_approved'),
        'rejected_requests': all_requests.filter(status='warden_rejected'),
        'returned_requests': all_requests.filter(status='returned'),
        'students_out_requests': all_requests.filter(status='security_approved'),
        'total_count': all_requests.count(),
    }
    return render(request, 'gatepass/warden_debug.html', context)


@login_required
def debug_info(request):
    """Debug information for testing"""
    if request.user.role != 'superadmin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Check for overdue returns
    check_overdue_returns()
    
    context = {
        'students': Student.objects.all(),
        'wardens': User.objects.filter(role='warden'),
        'security': User.objects.filter(role='security'),
        'gatepasses': GatePass.objects.all(),
        'notifications': Notification.objects.all(),
    }
    return render(request, 'gatepass/debug_info.html', context)