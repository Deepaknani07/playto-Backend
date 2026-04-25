from rest_framework import status
from rest_framework.test import APITestCase

from kyc.models import AppUser, KYCState, KYCSubmission, UserRole


class TransitionTests(APITestCase):
    def setUp(self):
        self.reviewer = AppUser.objects.create(username="rev", role=UserRole.REVIEWER, token="rev-token")
        self.merchant = AppUser.objects.create(username="mer", role=UserRole.MERCHANT, token="mer-token")
        self.submission = KYCSubmission.objects.create(merchant=self.merchant, state=KYCState.APPROVED)

    def test_illegal_transition_is_rejected(self):
        self.client.credentials(HTTP_X_AUTH_TOKEN=self.reviewer.token)
        response = self.client.post(
            f"/api/v1/reviewer/submissions/{self.submission.id}/transition",
            {"next_state": KYCState.DRAFT},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Illegal transition", str(response.data))
