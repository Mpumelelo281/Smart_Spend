from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import StudentProfile, User
from .utils import validate_dut_email


class RegisterSerializer(serializers.Serializer):
    """FR: student/parent/admin-style self-registration, gated to a DUT
    email domain, with format validation client-side-mirrored here because
    client-side checks are not trustworthy on their own (Rule 2).
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)
    campus = serializers.CharField(max_length=120)
    residence = serializers.CharField(max_length=120, required=False, allow_blank=True)
    disbursement_day = serializers.IntegerField(min_value=1, max_value=31, default=1)

    def validate_email(self, value):
        value = value.lower().strip()
        validate_dut_email(value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        campus = validated_data.pop("campus")
        residence = validated_data.pop("residence", "")
        disbursement_day = validated_data.pop("disbursement_day", 1)

        user = User.objects.create_user(email=validated_data["email"], password=password)
        StudentProfile.objects.create(
            user=user, campus=campus, residence=residence, disbursement_day=disbursement_day
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"].lower().strip(),
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid email or password.", code="authorization")
        if not user.email_verified:
            raise serializers.ValidationError("Please verify your email address before logging in.")
        attrs["user"] = user
        return attrs


class MFAChallengeSerializer(serializers.Serializer):
    login_token = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)


class MFASetupConfirmSerializer(serializers.Serializer):
    setup_token = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            "profile_id",
            "allowance_amount",
            "disbursement_day",
            "campus",
            "residence",
        ]
        read_only_fields = ["profile_id", "allowance_amount"]
