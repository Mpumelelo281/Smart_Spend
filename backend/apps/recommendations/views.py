from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent

from .engine import generate_for_profile
from .models import Preference, Recommendation
from .serializers import PreferenceSerializer, RecommendationFeedbackSerializer, RecommendationSerializer


class RecommendationListView(APIView):
    """Regenerates and returns the student's current recommendation batch
    on every GET — cheap (a handful of indexed queries over data the search
    page already keeps warm) and means a student never sees a stale batch
    from before they last edited their preferences.
    """

    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        profile = request.user.student_profile
        recommendations = generate_for_profile(profile)
        serializer = RecommendationSerializer(recommendations, many=True)
        return Response({"results": serializer.data})


class RecommendationFeedbackView(APIView):
    """Records whether the student acted on a recommendation — the ranking
    model's training signal (see Recommendation.was_accepted). Accepting or
    dismissing removes it from the next GET's pending batch since the
    filter in generate_for_profile only ever clears was_accepted-is-null
    rows.
    """

    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def post(self, request, recommendation_id):
        recommendation = get_object_or_404(
            Recommendation, recommendation_id=recommendation_id, profile__user=request.user
        )
        serializer = RecommendationFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recommendation.was_accepted = serializer.validated_data["was_accepted"]
        recommendation.save(update_fields=["was_accepted"])
        return Response(RecommendationSerializer(recommendation).data)


class PreferenceListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    serializer_class = PreferenceSerializer

    def get_queryset(self):
        return Preference.objects.filter(profile__user=self.request.user).order_by("pref_type")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["profile"] = self.request.user.student_profile
        return context


class PreferenceDetailView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get_object(self):
        return get_object_or_404(
            Preference, preference_id=self.kwargs["preference_id"], profile__user=self.request.user
        )

    def delete(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
