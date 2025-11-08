from rest_framework import serializers
from .models import User, Student, GatePass, ParentVerification


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'mobile_number', 'gender']


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'user', 'hall_ticket_no', 'student_name', 'room_no', 'parent_name', 'parent_mobile']


class GatePassSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Student.objects.all(), source='student')

    class Meta:
        model = GatePass
        fields = [
            'id', 'student', 'student_id', 'outing_date', 'outing_time', 'expected_return_date',
            'expected_return_time', 'purpose', 'status', 'warden_approval', 'security_approval',
            'actual_return_date', 'actual_return_time', 'created_at'
        ]


class ParentVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentVerification
        fields = ['id', 'gatepass', 'parent_mobile', 'verification_code', 'is_verified']
