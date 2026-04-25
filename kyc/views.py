from datetime import timedelta

from django.db.models import Avg, DurationField, ExpressionWrapper, F
from django.utils import timezone
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from kyc.models import AppUser, KYCState, KYCSubmission, UserRole
from kyc.permissions import IsMerchant, IsReviewer
from kyc.serializers import KYCSubmissionSerializer, TransitionSerializer, create_notification


def error_response(message: str, status_code: int):
    return Response({"error": {"message": message, "status_code": status_code}}, status=status_code)


@api_view(["POST"])
@permission_classes([])
def signup(request):
    username = request.data.get("username")
    role = request.data.get("role")
    if not username:
        return error_response("username is required", 400)
    if role not in {UserRole.MERCHANT, UserRole.REVIEWER}:
        return error_response("role must be merchant or reviewer", 400)
    if AppUser.objects.filter(username=username).exists():
        return error_response("username already exists", 400)
    user = AppUser.objects.create(
        username=username,
        role=role,
        token=f"{username}-{role}-token",
    )
    return Response({"id": user.id, "token": user.token, "role": user.role})


class MerchantSubmissionView(generics.ListCreateAPIView):
    serializer_class = KYCSubmissionSerializer
    permission_classes = [IsAuthenticated, IsMerchant]

    def get_queryset(self):
        return KYCSubmission.objects.filter(merchant_id=self.request.user.id).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(merchant_id=self.request.user.id, state=KYCState.DRAFT)


class MerchantSubmissionDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = KYCSubmissionSerializer
    permission_classes = [IsAuthenticated, IsMerchant]

    def get_queryset(self):
        return KYCSubmission.objects.filter(merchant_id=self.request.user.id)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsMerchant])
def merchant_submit(request, pk: int):
    try:
        submission = KYCSubmission.objects.get(pk=pk, merchant_id=request.user.id)
    except KYCSubmission.DoesNotExist:
        return error_response("Submission not found", 404)
    serializer = TransitionSerializer(data={"next_state": KYCState.SUBMITTED}, context={"submission": submission})
    serializer.is_valid(raise_exception=True)
    submission.state = KYCState.SUBMITTED
    submission.submitted_at = timezone.now()
    submission.mark_queue_time_if_needed()
    submission.save()
    create_notification(submission, "submission_submitted", {"submission_id": submission.id, "state": submission.state})
    return Response(KYCSubmissionSerializer(submission).data)


class ReviewerQueueView(generics.ListAPIView):
    serializer_class = KYCSubmissionSerializer
    permission_classes = [IsAuthenticated, IsReviewer]

    def get_queryset(self):
        return KYCSubmission.objects.filter(
            state__in=[KYCState.SUBMITTED, KYCState.UNDER_REVIEW]
        ).order_by("moved_to_queue_at", "created_at")


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsReviewer])
def reviewer_transition(request, pk: int):
    try:
        submission = KYCSubmission.objects.get(pk=pk)
    except KYCSubmission.DoesNotExist:
        return error_response("Submission not found", 404)

    serializer = TransitionSerializer(data=request.data, context={"submission": submission})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    next_state = data["next_state"]

    submission.state = next_state
    submission.reviewer_id = request.user.id
    submission.reviewer_note = data.get("reviewer_note", "")
    submission.mark_queue_time_if_needed()
    submission.save()

    create_notification(
        submission,
        "submission_state_changed",
        {
            "submission_id": submission.id,
            "state": submission.state,
            "reviewer_note": submission.reviewer_note,
        },
    )
    return Response(KYCSubmissionSerializer(submission).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsReviewer])
def reviewer_metrics(request):
    seven_days_ago = timezone.now() - timedelta(days=7)
    queue_qs = KYCSubmission.objects.filter(state__in=[KYCState.SUBMITTED, KYCState.UNDER_REVIEW])
    avg_queue_duration = queue_qs.aggregate(
        avg=Avg(ExpressionWrapper(timezone.now() - F("moved_to_queue_at"), output_field=DurationField()))
    )["avg"]
    recent = KYCSubmission.objects.filter(updated_at__gte=seven_days_ago)
    approved_count = recent.filter(state=KYCState.APPROVED).count()
    decision_count = recent.filter(state__in=[KYCState.APPROVED, KYCState.REJECTED]).count()
    approval_rate = (approved_count / decision_count * 100) if decision_count else 0.0
    at_risk_count = queue_qs.filter(moved_to_queue_at__lt=timezone.now() - timedelta(hours=24)).count()

    return Response(
        {
            "submissions_in_queue": queue_qs.count(),
            "average_time_in_queue_seconds": int(avg_queue_duration.total_seconds()) if avg_queue_duration else 0,
            "approval_rate_last_7_days": round(approval_rate, 2),
            "at_risk_count": at_risk_count,
        }
    )
