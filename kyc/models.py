from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    MERCHANT = "merchant", "Merchant"
    REVIEWER = "reviewer", "Reviewer"


class AppUser(models.Model):
    username = models.CharField(max_length=120, unique=True)
    token = models.CharField(max_length=120, unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices)

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"


class KYCState(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    UNDER_REVIEW = "under_review", "Under review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    MORE_INFO_REQUESTED = "more_info_requested", "More info requested"


def validate_file_size(file_obj):
    max_size_bytes = 5 * 1024 * 1024
    if file_obj.size > max_size_bytes:
        raise ValidationError("File size must not exceed 5 MB.")


class KYCSubmission(models.Model):
    merchant = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name="submissions")
    state = models.CharField(max_length=30, choices=KYCState.choices, default=KYCState.DRAFT)
    personal_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    business_name = models.CharField(max_length=200, blank=True)
    business_type = models.CharField(max_length=120, blank=True)
    expected_monthly_volume_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pan_document = models.FileField(
        upload_to="documents/",
        blank=True,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]), validate_file_size],
    )
    aadhaar_document = models.FileField(
        upload_to="documents/",
        blank=True,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]), validate_file_size],
    )
    bank_statement_document = models.FileField(
        upload_to="documents/",
        blank=True,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]), validate_file_size],
    )
    reviewer = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_submissions",
    )
    reviewer_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    moved_to_queue_at = models.DateTimeField(null=True, blank=True)

    def mark_queue_time_if_needed(self):
        if self.state in {KYCState.SUBMITTED, KYCState.UNDER_REVIEW} and not self.moved_to_queue_at:
            self.moved_to_queue_at = timezone.now()


class NotificationEvent(models.Model):
    merchant = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name="notifications")
    event_type = models.CharField(max_length=80)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
