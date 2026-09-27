from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent

from . import engine
from .serializers import AssistantMessageSerializer


class AssistantAskView(APIView):
    """SpendWise chat endpoint: one message in, one templated reply out —
    see engine.py for why this is rule-based rather than an LLM call.
    Scoped to the asking student's own StudentProfile the same way every
    other student-facing view in this project is (Rule 9); there is no
    path here that can read another student's data.
    """

    permission_classes = [permissions.IsAuthenticated, IsStudent]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "assistant"

    def post(self, request):
        serializer = AssistantMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = engine.answer(serializer.validated_data["message"], request.user.student_profile)
        return Response(
            {
                "reply": result.reply,
                "intent": result.intent,
                "quick_replies": result.quick_replies,
            }
        )
