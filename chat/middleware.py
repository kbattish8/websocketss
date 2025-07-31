# chat/middleware.py
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app  

    async def __call__(self, scope, receive, send):
       
        query_string = parse_qs(scope.get("query_string", b"").decode())
        token = query_string.get("token", [None])[0]

        if token:
            try:
                access_token = AccessToken(token)  
                user_id = access_token["user_id"]
                scope["user"] = await get_user(user_id)
            except Exception as e:
                print("JWTAuthMiddleware error:", e)
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        # Call inner ASGI app
        return await self.app(scope, receive, send)
