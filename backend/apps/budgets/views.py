from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.accounts.permissions import IsStudent

from .models import Budget, Transaction
from .serializers import BudgetCreateSerializer, BudgetSerializer, TransactionSerializer


class BudgetListCreateView(generics.ListCreateAPIView):
    """Rule 9: RBAC enforced here via permission_classes, not by the client
    hiding the "create budget" button — a Student can only ever see/create
    budgets tied to their own StudentProfile (see get_queryset).
    """

    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get_queryset(self):
        return Budget.objects.filter(profile__user=self.request.user).order_by("-year", "-month")

    def get_serializer_class(self):
        return BudgetCreateSerializer if self.request.method == "POST" else BudgetSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == "POST":
            context["profile"] = self.request.user.student_profile
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        budget = serializer.save()
        return Response(BudgetSerializer(budget).data, status=status.HTTP_201_CREATED)


class BudgetDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    serializer_class = BudgetSerializer

    def get_queryset(self):
        return Budget.objects.filter(profile__user=self.request.user)

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])


class TransactionCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
