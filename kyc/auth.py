from dataclasses import dataclass

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from kyc.models import AppUser, UserRole


@dataclass
class SimpleAuthUser:
    id: int
    username: str
    role: str
    token: str
    is_authenticated: bool = True


class SimpleHeaderAuthentication(BaseAuthentication):
    DEMO_TOKENS = {
        "merchant-draft-token": {"username": "merchant_draft", "role": UserRole.MERCHANT},
        "merchant-under-review-token": {"username": "merchant_under_review", "role": UserRole.MERCHANT},
        "reviewer-token": {"username": "reviewer1", "role": UserRole.REVIEWER},
    }

    def authenticate(self, request):
        token = request.headers.get("X-Auth-Token")
        if not token:
            return None
        try:
            db_user = AppUser.objects.get(token=token)
        except AppUser.DoesNotExist:
            demo_user = self.DEMO_TOKENS.get(token)
            if not demo_user:
                raise AuthenticationFailed("Invalid token.")
            db_user, _ = AppUser.objects.get_or_create(
                username=demo_user["username"],
                defaults={"token": token, "role": demo_user["role"]},
            )
            # Ensure the user keeps the expected demo token/role if row pre-existed.
            if db_user.token != token or db_user.role != demo_user["role"]:
                db_user.token = token
                db_user.role = demo_user["role"]
                db_user.save(update_fields=["token", "role"])

        user = SimpleAuthUser(
            id=db_user.id,
            username=db_user.username,
            role=db_user.role,
            token=db_user.token,
        )
        return (user, None)
