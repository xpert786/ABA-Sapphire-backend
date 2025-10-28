from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    Token can be passed as a query parameter: ws://url/?token=<jwt_token>
    """

    async def __call__(self, scope, receive, send):
        # Get query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        # Get token from query parameters
        token = query_params.get('token', [None])[0]
        
        print(f"🔐 JWT Auth Middleware - Query string: {query_string}")
        print(f"🔐 Token present: {bool(token)}")
        
        if token:
            try:
                # Validate token and get user
                access_token = AccessToken(token)
                user = await self.get_user_from_token(access_token)
                scope['user'] = user
                print(f"[SUCCESS] Authenticated user: {user.username}")
            except Exception as e:
                print(f"[ERROR] Token validation failed: {e}")
                scope['user'] = AnonymousUser()
        else:
            print(f"[ERROR] No token provided in query string")
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, access_token):
        """Get user from validated JWT token"""
        user_id = access_token.payload.get('user_id')
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()

