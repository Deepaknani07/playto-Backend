from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import kyc.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AppUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(max_length=120, unique=True)),
                ("token", models.CharField(max_length=120, unique=True)),
                ("role", models.CharField(choices=[("merchant", "Merchant"), ("reviewer", "Reviewer")], max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name="NotificationEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=80)),
                ("payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "merchant",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="kyc.appuser"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="KYCSubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("submitted", "Submitted"),
                            ("under_review", "Under review"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("more_info_requested", "More info requested"),
                        ],
                        default="draft",
                        max_length=30,
                    ),
                ),
                ("personal_name", models.CharField(blank=True, max_length=200)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("business_name", models.CharField(blank=True, max_length=200)),
                ("business_type", models.CharField(blank=True, max_length=120)),
                ("expected_monthly_volume_usd", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                (
                    "pan_document",
                    models.FileField(
                        blank=True,
                        upload_to="documents/",
                        validators=[django.core.validators.FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]), kyc.models.validate_file_size],
                    ),
                ),
                (
                    "aadhaar_document",
                    models.FileField(
                        blank=True,
                        upload_to="documents/",
                        validators=[django.core.validators.FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]), kyc.models.validate_file_size],
                    ),
                ),
                (
                    "bank_statement_document",
                    models.FileField(
                        blank=True,
                        upload_to="documents/",
                        validators=[django.core.validators.FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]), kyc.models.validate_file_size],
                    ),
                ),
                ("reviewer_note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("moved_to_queue_at", models.DateTimeField(blank=True, null=True)),
                ("merchant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="submissions", to="kyc.appuser")),
                (
                    "reviewer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_submissions",
                        to="kyc.appuser",
                    ),
                ),
            ],
        ),
    ]
