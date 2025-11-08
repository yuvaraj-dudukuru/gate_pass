# Hostel Gatepass Management System

A comprehensive Django-based web application for managing student gatepass requests in hostels with role-based authentication and approval workflows.

## Features

### 🎯 Core Functionality
- **Role-based Authentication**: Super Admin, Warden, Security, and Student roles
- **Student Registration**: Automatic username generation (Name@last4digits)
- **Gatepass Request System**: Complete workflow from request to approval
- **Parent Verification**: SMS-based verification system
- **Gender-based Routing**: Automatic routing to appropriate wardens (boys/girls)
- **Real-time Notifications**: Status updates for all stakeholders

### 👥 User Roles

#### Super Admin
- Full system access and control
- User registration approval/rejection
- Django admin panel access
- System management capabilities

#### Student
- Register with detailed information (Hall ticket, room number, parent details)
- Request gatepass for outings
- View request status and history
- Automatic username format: `Name@last4digits`

#### Warden
- Approve/reject student gatepass requests
- Parent verification confirmation
- Gender-based request routing
- Detailed student information access

#### Security
- Final gate approval
- Student identity verification
- Gate access management
- Exit approval system

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- Django 5.2+

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hostel-gatepass
   ```

2. **Install dependencies**
   ```bash
   pip install django
   ```

3. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start development server**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   - Main application: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## 📋 Default Login Credentials

- **Super Admin**: 
  - Username: `admin`
  - Password: `admin123`
  - Email: `admin@hostel.com`

## 🔄 Workflow

### Student Registration Process
1. Student fills registration form with:
   - Hall ticket number
   - Student name
   - Room number
   - Parent name and mobile
   - Email and mobile (optional)
   - Gender
2. Username automatically generated as `Name@last4digits`
3. Super admin approves/rejects registration

### Gatepass Request Process
1. **Student Request**: Student submits outing details
2. **Parent Verification**: Parent receives verification code
3. **Warden Approval**: Warden reviews and approves/rejects
4. **Security Approval**: Security grants final gate access
5. **Completion**: Student can leave campus

### Gender-based Routing
- Male students → Male warden
- Female students → Female warden
- Automatic routing based on student gender

## 🗄️ Database Models

### User Model (Custom)
- Role-based authentication
- Email and mobile uniqueness
- Gender specification
- Approval status

### Student Model
- Hall ticket number (unique)
- Room number
- Parent information
- Parent mobile (unique)

### GatePass Model
- Outing details (date, time, purpose)
- Status tracking
- Approval workflow
- Parent verification

### Additional Models
- Warden, Security profiles
- Parent verification
- Notifications system

## 🎨 UI Features

- **Responsive Design**: Bootstrap 5 integration
- **Modern Interface**: Clean and intuitive design
- **Role-based Navigation**: Dynamic menu based on user role
- **Status Indicators**: Color-coded status badges
- **Form Validation**: Client and server-side validation
- **Mobile-friendly**: Responsive design for all devices

## 🔒 Security Features

- **Unique Constraints**: Mobile numbers and hall tickets
- **Role-based Access**: Restricted access based on user role
- **Parent Verification**: SMS-based verification system
- **Password Validation**: Strong password requirements
- **CSRF Protection**: Django's built-in CSRF protection

## 📱 Parent Verification System

1. Student submits gatepass request
2. System generates 6-digit verification code
3. Parent receives code via SMS (simulated)
4. Parent enters code on verification page
5. Warden confirms parent verification before approval

## 🛠️ Admin Panel Features

- **User Management**: Approve/reject registrations
- **Gatepass Monitoring**: Track all requests
- **System Statistics**: User counts and status
- **Direct Database Access**: Full CRUD operations
- **Bulk Operations**: Mass approval/rejection

## 📊 Key Features Implemented

✅ **Complete Registration System**
✅ **Role-based Authentication**
✅ **Gatepass Request Workflow**
✅ **Parent Verification System**
✅ **Gender-based Warden Routing**
✅ **Security Gate Management**
✅ **Admin Panel Integration**
✅ **Responsive UI Design**
✅ **Database Relationships**
✅ **Form Validation**

## 🔧 Technical Stack

- **Backend**: Django 5.2
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Database**: SQLite (development)
- **Authentication**: Django's custom user model
- **Templates**: Django template engine
- **Icons**: Font Awesome 6

## 📝 Usage Instructions

### For Students
1. Register with your details
2. Wait for admin approval
3. Login with generated username
4. Submit gatepass requests
5. Track request status

### For Wardens
1. Register and wait for approval
2. Login to dashboard
3. Review pending requests
4. Verify parent approval
5. Approve/reject requests

### For Security
1. Register and wait for approval
2. Login to dashboard
3. View approved requests
4. Verify student identity
5. Grant gate access

### For Super Admin
1. Login with admin credentials
2. Approve user registrations
3. Monitor system activity
4. Access Django admin panel
5. Manage system settings

## 🚨 Important Notes

- Mobile numbers must be unique across the system
- Hall ticket numbers must be unique
- Parent verification is required for approval
- Gender-based routing is automatic
- All timestamps are tracked for audit purposes

## 🔮 Future Enhancements

- SMS integration for real parent verification
- Email notifications
- Mobile app development
- Advanced reporting and analytics
- Integration with hostel management systems
- QR code generation for gatepasses

## 📞 Support

For technical support or questions about the system, please contact the development team or refer to the Django documentation.

---

**Developed with ❤️ using Django**
