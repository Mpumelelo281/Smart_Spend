from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from .models import StudentProfile, User
from .utils import validate_dut_email


class RegisterSerializer(serializers.Serializer):
    """FR: student/parent/admin-style self-registration, gated to a DUT
    email domain, with format validation client-side-mirrored here because
    client-side checks are not trustworthy on their own (Rule 2).

    popia_consent is required, not optional: POPIA requires consent to
    exist before personal information (email, campus, residence below) is
    collected, so this is checked before create() ever runs — there is no
    path that stores a profile without a recorded consent timestamp.
    """

    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)
    campus = serializers.CharField(max_length=120)
    residence = serializers.CharField(max_length=120, required=False, allow_blank=True)
    disbursement_day = serializers.IntegerField(min_value=1, max_value=31, default=1)
    popia_consent = serializers.BooleanField(write_only=True)

    def validate_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Full name is required.")
        return value

    def validate_email(self, value):
        value = value.lower().strip()
        validate_dut_email(value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_popia_consent(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must agree to the Privacy Policy to create an account."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        full_name = validated_data.pop("full_name")
        campus = validated_data.pop("campus")
        residence = validated_data.pop("residence", "")
        disbursement_day = validated_data.pop("disbursement_day", 1)
        validated_data.pop("popia_consent")

        user = User.objects.create_user(
            email=validated_data["email"], password=password, popia_consent_at=timezone.now()
        )
        StudentProfile.objects.create(
            user=user,
            full_name=full_name,
            campus=campus,
            residence=residence,
            disbursement_day=disbursement_day,
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
            "full_name",
            "allowance_amount",
            "disbursement_day",
            "campus",
            "residence",
        ]
        read_only_fields = ["profile_id", "allowance_amount"]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=10)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, user=self.context["request"].user)
        return value


class MFAResetSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=10)
