from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings


COOKIE_NAME = 'pet_shelter_refresh'
COOKIE_PATH = '/api/auth/session/'


def set_refresh_cookie(response, token):
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        path=COOKIE_PATH,
        secure=not settings.DEBUG,
        httponly=True,
        samesite='Lax',
    )


@method_decorator([never_cache, csrf_protect], name='dispatch')
class BrowserSessionView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request):
        csrf_token = get_token(request)
        refresh = request.COOKIES.get(COOKIE_NAME)
        if not refresh:
            return Response({'access': None, 'csrfToken': csrf_token})

        serializer = TokenRefreshSerializer(data={'refresh': refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except (AuthenticationFailed, ObjectDoesNotExist, TokenError):
            response = Response({'access': None, 'csrfToken': csrf_token})
            response.delete_cookie(COOKIE_NAME, path=COOKIE_PATH, samesite='Lax')
            return response

        tokens = serializer.validated_data
        response = Response({'access': tokens['access'], 'csrfToken': csrf_token})
        if tokens.get('refresh'):
            set_refresh_cookie(response, tokens['refresh'])
        return response

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data
        response = Response({'access': tokens['access']})
        set_refresh_cookie(response, tokens['refresh'])
        return response

    def delete(self, request):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(COOKIE_NAME, path=COOKIE_PATH, samesite='Lax')
        return response
