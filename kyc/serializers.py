from datetime import timedelta

from django.core.files.images import get_image_dimensions
from django.utils import timezone
from rest_framework import serializers

from kyc.models import AppUser, KYCState, KYCSubmission, NotificationEvent
from kyc.state_machine import ensure_valid_transition


class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ["id", "username", "role", "token"]


class KYCSubmissionSerializer(serializers.ModelSerializer):
    at_risk = serializers.SerializerMethodField()

    class Meta:
        model = KYCSubmission
        fields = [
            "id",
            "merchant",
            "state",
            "personal_name",
            "email",
            "phone",
            "business_name",
            "business_type",
            "expected_monthly_volume_usd",
            "pan_document",
            "aadhaar_document",
            "bank_statement_document",
            "reviewer",
            "reviewer_note",
            "created_at",
            "updated_at",
            "submitted_at",
            "moved_to_queue_at",
            "at_risk",
        ]
        read_only_fields = ["merchant", "created_at", "updated_at", "submitted_at", "moved_to_queue_at", "at_risk"]

    def get_at_risk(self, obj):
        if not obj.moved_to_queue_at or obj.state not in {KYCState.SUBMITTED, KYCState.UNDER_REVIEW}:
            return False
        return timezone.now() - obj.moved_to_queue_at > timedelta(hours=24)

    def validate(self, attrs):
        # Extra defense to ensure image files are actual images where applicable.
        for field in ["pan_document", "aadhaar_document", "bank_statement_document"]:
            file_obj = attrs.get(field)
            if file_obj and file_obj.name.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    get_image_dimensions(file_obj)
                except Exception as exc:
                    raise serializers.ValidationError({field: "Invalid image file."}) from exc
        return attrs


class TransitionSerializer(serializers.Serializer):
    next_state = serializers.ChoiceField(choices=KYCState.choices)
    reviewer_note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        submission = self.context["submission"]
        next_state = attrs["next_state"]
        try:
            ensure_valid_transition(submission.state, next_state)
        except ValueError as exc:
            raise serializers.ValidationError({"next_state": str(exc)}) from exc
        if next_state in {KYCState.REJECTED, KYCState.MORE_INFO_REQUESTED} and not attrs.get("reviewer_note"):
            raise serializers.ValidationError({"reviewer_note": "Reason is required for rejection or more-info request."})
        return attrs


def create_notification(submission: KYCSubmission, event_type: str, payload: dict):
    NotificationEvent.objects.create(
        merchant=submission.merchant,
        event_type=event_type,
        payload=payload,
    )
