from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home and Authentication
    path('', views.CustomLoginView.as_view(), name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('logout/confirm/', views.logout_confirm, name='logout_confirm'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('register/', views.register, name='register'),
    
    # Registration URLs
    path('register/student/', views.register_student, name='register_student'),
    path('register/warden/', views.register_warden, name='register_warden'),
    path('register/security/', views.register_security, name='register_security'),
    
    # Dashboard URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('warden/dashboard/', views.warden_dashboard, name='warden_dashboard'),
    path('security/dashboard/', views.security_dashboard, name='security_dashboard'),
    path('superadmin/dashboard/', views.superadmin_dashboard, name='superadmin_dashboard'),
    
    # Gatepass URLs
    path('student/gatepass/create/', views.create_gatepass, name='create_gatepass'),
    path('warden/gatepass/<int:gatepass_id>/approve/', views.warden_approve_gatepass, name='warden_approve_gatepass'),
    path('security/gatepass/<int:gatepass_id>/approve/', views.security_approve_gatepass, name='security_approve_gatepass'),
    path('security/gatepass/<int:gatepass_id>/return/', views.security_record_return, name='security_record_return'),
    
    # User Management URLs
    path('superadmin/user/<int:user_id>/approve/', views.approve_user, name='approve_user'),
    path('superadmin/user/<int:user_id>/reject/', views.reject_user, name='reject_user'),
    
    # Super Admin Gatepass URLs
    path('superadmin/gatepass/<int:gatepass_id>/approve/', views.superadmin_approve_gatepass, name='superadmin_approve_gatepass'),
    
    # Parent Verification
    path('parent/verify/<int:gatepass_id>/', views.parent_verification, name='parent_verification'),
    
    # Debug URLs
    path('debug/', views.debug_info, name='debug_info'),
    path('warden/debug/', views.warden_debug, name='warden_debug'),
]

# --- API endpoints for mobile clients ---
from . import api_views

urlpatterns += [
    path('api/login/', api_views.LoginAPIView.as_view(), name='api_login'),
    path('api/gatepasses/', api_views.GatePassListCreateAPIView.as_view(), name='api_gatepass_list_create'),
    path('api/gatepasses/<int:pk>/warden-approve/', api_views.WardenApproveAPIView.as_view(), name='api_warden_approve'),
    path('api/gatepasses/<int:pk>/security-approve/', api_views.SecurityApproveAPIView.as_view(), name='api_security_approve'),
]
