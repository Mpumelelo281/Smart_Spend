"""
Authentication flow (FR: login for students/parents/admin; NFR: TOTP MFA;
Rule 8: audit log every auth event; Rule 9: RBAC is enforced by
permission_classes on every view, never assumed from the UI).

Two-step login, always:
  1. POST /login/            email + password
       -> mfa_enabled=False: {"mfa_setup_required": true, "setup_token",
                               "provisioning_uri", "qr_code_base64"}
       -> mfa_enabled=True:  {"mfa_required": true, "login_token"}
  2a. POST /mfa/setup/confirm/   setup_token + code  -> JWT pair, mfa now on
  2b. POST /mfa/verify/          login_token + code  -> JWT pair

No bearer token is ever issued from step 1 alone.
"""

import base64
from io import BytesIO

import qrcode
from django.core.mail import send_mail
from django.conf import settings
from django.core import signing
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .audit import log_action
from .models import StudentProfile, User
from .serializers import (
    LoginSerializer,
    MFAChallengeSerializer,
    MFASetupConfirmSerializer,
    RegisterSerializer,
    StudentProfileSerializer,
    VerifyEmailSerializer,
)
from .tokens import issue_login_challenge, issue_setup_challenge, read_login_challenge, read_setup_challenge
from .utils import generate_mfa_secret, provisioning_uri, verify_totp_code


def _issue_jwt_pair(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _qr_png_base64(uri: str) -> str:
    img = qrcode.make(uri)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if settings.SKIP_AUTH_VERIFICATION_FOR_TESTING:
            # Local-testing-only escape hatch — see LoginView below and
            # .env.example. Never true outside a developer's own machine.
            user.email_verified = True
            user.status = User.Status.ACTIVE
            user.save(update_fields=["email_verified", "status", "updated_at"])
            log_action("USER_REGISTERED", actor=user, target=user, metadata={"email": user.email})
            return Response(
                {"detail": "Registration successful. Email verification skipped (testing mode)."},
                status=status.HTTP_201_CREATED,
            )

        verify_url = f"{settings.FRONTEND_BASE_URL}/verify-email?token={user.email_verification_token}"
        send_mail(
            subject="Verify your SmartSpend account",
            message=f"Welcome to SmartSpend. Verify your account: {verify_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        log_action("USER_REGISTERED", actor=user, target=user, metadata={"email": user.email})
        return Response(
            {"detail": "Registration successful. Check your DUT email to verify your account."},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, email_verification_token=serializer.validated_data["token"])

        user.email_verified = True
        user.status = User.Status.ACTIVE
        user.save(update_fields=["email_verified", "status", "updated_at"])
        log_action("EMAIL_VERIFIED", actor=user, target=user)
        return Response({"detail": "Email verified. You can now log in."})


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            log_action("LOGIN_FAILED", metadata={"email": request.data.get("email", "")})
            raise

        user = serializer.validated_data["user"]

        if settings.SKIP_AUTH_VERIFICATION_FOR_TESTING:
            # Local-testing-only escape hatch (see RegisterView and
            # .env.example) — issues tokens straight after the password
            # check, same as a normal login would after MFA succeeds. Never
            # true outside a developer's own machine: this is the actual
            # NFR Security control (TOTP MFA) being switched off, not a
            # cosmetic shortcut.
            log_action("LOGIN_SUCCESS", actor=user, target=user, metadata={"mfa_skipped": True})
            return Response(_issue_jwt_pair(user))

        if not user.mfa_enabled:
            secret = generate_mfa_secret()
            uri = provisioning_uri(user.email, secret)
            setup_token = issue_setup_challenge(user.user_id, secret)
            log_action("MFA_SETUP_ISSUED", actor=user, target=user)
            return Response(
                {
                    "mfa_setup_required": True,
                    "setup_token": setup_token,
                    "provisioning_uri": uri,
                    "qr_code_base64": _qr_png_base64(uri),
                }
            )

        login_token = issue_login_challenge(user.user_id)
        log_action("MFA_CHALLENGE_ISSUED", actor=user, target=user)
        return Response({"mfa_required": True, "login_token": login_token})


class MFASetupConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "mfa"

    def post(self, request):
        serializer = MFASetupConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = read_setup_challenge(serializer.validated_data["setup_token"])
        except signing.BadSignature:
            return Response(
                {"detail": "Setup session expired. Log in again."}, status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, user_id=payload["user_id"])
        if not verify_totp_code(payload["secret"], serializer.validated_data["code"]):
            log_action("MFA_SETUP_FAILED", actor=user, target=user)
            return Response({"detail": "Incorrect code."}, status=status.HTTP_400_BAD_REQUEST)

        user.mfa_secret = payload["secret"]
        user.mfa_enabled = True
        user.save(update_fields=["mfa_secret", "mfa_enabled", "updated_at"])
        log_action("MFA_ENABLED", actor=user, target=user)
        log_action("LOGIN_SUCCESS", actor=user, target=user)
        return Response(_issue_jwt_pair(user))


class MFAVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "mfa"

    def post(self, request):
        serializer = MFAChallengeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_id = read_login_challenge(serializer.validated_data["login_token"])
        except signing.BadSignature:
            return Response(
                {"detail": "Login session expired. Log in again."}, status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, user_id=user_id)
        if not verify_totp_code(user.mfa_secret, serializer.validated_data["code"]):
            log_action("MFA_FAILED", actor=user, target=user)
            return Response({"detail": "Incorrect code."}, status=status.HTTP_401_UNAUTHORIZED)

        log_action("LOGIN_SUCCESS", actor=user, target=user)
        return Response(_issue_jwt_pair(user))


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass
        log_action("LOGOUT", actor=request.user, target=request.user)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = StudentProfile.objects.filter(user=user).first()
        return Response(
            {
                "user_id": str(user.user_id),
                "email": user.email,
                "role": user.role,
                "status": user.status,
                "profile": StudentProfileSerializer(profile).data if profile else None,
            }
        )
