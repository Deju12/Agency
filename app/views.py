from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import User
from django.db import connection, OperationalError
from django.db.models import Q

def response(status, code, message, data=None):
    """Generate a standardized JSON API response."""
    return JsonResponse({
        "status": status,  # "success" or "error"
        "code": code,      # HTTP status code
        "message": message,
        "data": data
    }, status=code)

def check_db_connection(request):
    try:
        connection.ensure_connection()
        return response("success", 200, "Connected to PostgreSQL database")
    except OperationalError as e:
        return response("error", 500, "Connection failed", {"error": str(e)})

@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return response("error", 405, "Only POST method allowed")

    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        user = User.objects.filter(username=username, password=password).first()
        notfound = User.objects.exclude(username=username).exclude(password=password)
        usernotfound= User.objects.exclude(username=username)
        passnotfound= User.objects.exclude(password=password)

        if user:
            return response("success", 200, "Login successful", {
                "username": user.username,
                "role": user.role
            })
        elif usernotfound.exists():
            return response("fail", 404, "User not found")
        elif passnotfound.exists():
            return response("fail", 404, "Invalid password")
        else:
            return response("error", 401, "unautorized access")
    except Exception as e:
        return response("error", 400, "Bad request", {"error": str(e)})

@csrf_exempt
def forgot_password_view(request):
    if request.method != "POST":
        return response("error", 405, "Only POST method allowed")

    try:
        data = json.loads(request.body)
        username = data.get("username")
        forgot_key = data.get("forgot_key")
        new_password = data.get("new_password")

        user = User.objects.filter(username=username, forgot_key=forgot_key).first()

        if user:
            user.password = new_password
            user.save()
            return response("success", 200, "Password updated successfully")
        else:
            return response("error", 401, "Invalid username or forgot key")
    except Exception as e:
        return response("error", 400, "Bad request", {"error": str(e)})
