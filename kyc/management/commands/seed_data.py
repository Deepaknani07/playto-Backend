from django.core.management.base import BaseCommand

from kyc.models import AppUser, KYCState, KYCSubmission, UserRole


class Command(BaseCommand):
    help = "Seed DB with 2 merchants and 1 reviewer."

    def handle(self, *args, **options):
        m1, _ = AppUser.objects.get_or_create(
            username="merchant_draft",
            defaults={"role": UserRole.MERCHANT, "token": "merchant-draft-token"},
        )
        m2, _ = AppUser.objects.get_or_create(
            username="merchant_under_review",
            defaults={"role": UserRole.MERCHANT, "token": "merchant-under-review-token"},
        )
        r1, _ = AppUser.objects.get_or_create(
            username="reviewer1",
            defaults={"role": UserRole.REVIEWER, "token": "reviewer-token"},
        )

        KYCSubmission.objects.get_or_create(
            merchant=m1,
            defaults={"state": KYCState.DRAFT, "business_name": "Draft Studio"},
        )
        KYCSubmission.objects.get_or_create(
            merchant=m2,
            defaults={
                "state": KYCState.UNDER_REVIEW,
                "business_name": "Global Agency",
                "reviewer": r1,
            },
        )
        self.stdout.write(self.style.SUCCESS("Seed complete."))
