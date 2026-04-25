from dataclasses import dataclass

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from kyc.models import AppUser


@dataclass
class SimpleAuthUser:
    id: int
    username: str
    role: str
    token: str
    is_authenticated: bool = True


class SimpleHeaderAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get("X-Auth-Token")
        if not token:
            return None
        try:
            db_user = AppUser.objects.get(token=token)
        except AppUser.DoesNotExist as exc:
            raise AuthenticationFailed("Invalid token.") from exc

        user = SimpleAuthUser(
            id=db_user.id,
            username=db_user.username,
            role=db_user.role,
            token=db_user.token,
        )
        return (user, None)
