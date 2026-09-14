from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from kava_varasto.whatsnew import CURRENT_VERSION, WHATS_NEW, is_unseen

from .permissions import IsAuthenticatedAndPasswordCurrent
from .serializers import (
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
    UserSerializer,
)
from .throttling import LoginRateThrottle


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CurrentUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"authenticated": False, "user": None})
        return Response({"authenticated": True, "user": UserSerializer(request.user).data})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials."}, status=400)
        login(request, user)
        return Response({"authenticated": True, "user": UserSerializer(user).data})


class LogoutView(APIView):
    # Plain IsAuthenticated: a user who owes a password change must still be
    # able to log out (the default permission class denies them everything).
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=204)


class ChangePasswordView(APIView):
    # Plain IsAuthenticated: this is the endpoint that clears
    # must_change_password, so it cannot require the flag to be clear.
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        update_session_auth_hash(request, request.user)
        return Response({"authenticated": True, "user": UserSerializer(request.user).data})


class ProfileView(APIView):
    # This is the project's DEFAULT_PERMISSION_CLASSES anyway; spelled out
    # here because, unlike its /me/ and change-password neighbours, this
    # endpoint is deliberately *not* one of the exceptions that stays open
    # to a user who still owes a password change.
    #
    # No @csrf_protect: this is an authenticated write, same shape as
    # ChangePasswordView. SessionAuthentication.authenticate() already calls
    # enforce_csrf() whenever it finds an active session user -- the
    # decorator is only needed on AllowAny/pre-auth views like LoginView,
    # where authenticate() returns before reaching that call.
    permission_classes = [IsAuthenticatedAndPasswordCurrent]

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"authenticated": True, "user": UserSerializer(request.user).data})


class WhatsNewView(APIView):
    # Same permission class as ProfileView, for the same reason: this isn't
    # one of the deliberate exceptions that stays open to an account owing a
    # password change.
    #
    # No @csrf_protect on the POST: same reasoning as ProfileView above --
    # SessionAuthentication.authenticate() already enforces CSRF for an
    # authenticated session.
    permission_classes = [IsAuthenticatedAndPasswordCurrent]

    def get(self, request):
        # "unseen" is computed here, not left for the frontend to work out
        # from whats_new_seen_version + entries -- there is no JS test suite
        # to catch a regression in that comparison, so the one place it's
        # tested (is_unseen, directly) is also the one place it runs.
        return Response(
            {
                "current_version": CURRENT_VERSION,
                "unseen": is_unseen(request.user.whats_new_seen_version),
                "entries": WHATS_NEW,
            }
        )

    def post(self, request):
        # Stamping happens only here, on explicit acknowledgement -- never as
        # a side effect of GET or of login -- so a refresh before the user
        # has actually read the dialog can't lose it.
        request.user.whats_new_seen_version = CURRENT_VERSION
        request.user.save(update_fields=["whats_new_seen_version"])
        return Response({"authenticated": True, "user": UserSerializer(request.user).data})
