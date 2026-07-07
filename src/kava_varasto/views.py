from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def spa(request):
    return render(request, "spa.html", {"script_name": request.META.get("SCRIPT_NAME", "")})
