from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.files.base import ContentFile
import base64
from psycopg import Transaction
from requests import Response, request
from .models import Applicant, OtherInformation, Relative, SkillsExperience, SponsorVisa, User, ApplicantSelection
from django.db import connection, OperationalError
from django.db.models import Q
from datetime import date
from django.utils import timezone
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ApplicantSelection
from .serializers import ApplicantSelectionSerializer
from rest_framework import status

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
#GET user
def get_all_users(request):
    if request.method != "GET":
        return JsonResponse({"status": "fail", "code": 405, "message": "Method not allowed"})
    try:
        users = User.objects.all()
        data = []
        role = request.GET.get('role')
        if role:
            users = users.filter(role=role)
        for u in users:
            data.append({
                "id": u.id,
                "username": u.username,
                "password":u.password,
                "role": u.role,
                "forgot_key": u.forgot_key,
            })

        return JsonResponse({
            "status": "success",
            "code": 200,
            "message": "Users fetched",
            "data": data
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "code": 400,
            "message": "Bad request",
            "data": {"error": str(e)}
        })
        
@csrf_exempt
def create_user(request):
    if request.method != "POST":
        return JsonResponse({"status": "fail", "code": 405, "message": "Method not allowed"})
    try:
        body = json.loads(request.body)
        username = body.get("username")
        password = body.get("password")
        role = body.get("role")
        forgot_key = body.get("forgot_key")

        if not all([username, password, role]):
            return JsonResponse({"status": "fail", "code": 400, "message": "Missing required fields"})

        # check if role is valid
        valid_roles = dict(User.ROLE_CHOICES).keys()
        if role not in valid_roles:
            return JsonResponse({
                "status": "fail",
                "code": 400,
                "message": f"Invalid role. Must be one of {list(valid_roles)}"
            })
            
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                "status": "fail",
                "code": 400,
                "message": "Username already taken"
            })

        # Hash password instead of storing plain text
        user = User.objects.create(
            username=username,
            password=password,  # secure password
            role=role,
            forgot_key = forgot_key
        )

        return JsonResponse({
            "status": "success",
            "code": 201,
            "message": "User created",
            "data": {"id": user.id}
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "code": 400,
            "message": "Bad request",
            "data": {"error": str(e)}
        })

# UPDATE user
@csrf_exempt
def update_user(request, user_id):
    if request.method != "PUT":
        return JsonResponse({"status": "fail", "code": 405, "message": "Method not allowed"})
    try:
        user = User.objects.filter(username=user_id).first()
        if not user:
            return JsonResponse({"status": "fail", "code": 404, "message": "User not found"})

        body = json.loads(request.body)
        user.username = body.get("username", user.username)
        user.password = body.get("password", user.password)
        user.role = body.get("role", user.role)
        user.forgot_key = body.get("forgot_key", user.forgot_key)
        user.save()

        return JsonResponse({"status": "success", "code": 200, "message": "User updated"})
    except Exception as e:
        return JsonResponse({"status": "error", "code": 400, "message": "Bad request", "data": {"error": str(e)}})

# DELETE user
@csrf_exempt
def delete_user(request, user_id):
    if request.method != "DELETE":
        return JsonResponse({"status": "fail", "code": 405, "message": "Method not allowed"})
    try:
        user = User.objects.filter(username=user_id).first()
        if not user:
            return JsonResponse({"status": "fail", "code": 404, "message": "User not found"})
        user.delete()
        return JsonResponse({"status": "success", "code": 200, "message": "User deleted"})
    except Exception as e:
        return JsonResponse({"status": "error", "code": 400, "message": "Bad request", "data": {"error": str(e)}})
    
    
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

# Create Applicant
@csrf_exempt
def create_applicant(request):
    if request.method != "POST":
        return response("error", 405, "Only POST allowed")
    
    try:
        data = json.loads(request.body)
        applicant_data = data.get("applicant", {})
        photo = applicant_data.get("photo")  # should be a full base64 string
        full_photo = applicant_data.get("full_photo")
        passport_photo = applicant_data.get("passport_photo")
        print("Photo length:", len(applicant_data.get("photo", "")))
        print("Full Photo length:", len(applicant_data.get("full_photo", "")))
        print("Passport Photo length:", len(applicant_data.get("passport_photo", "")))

        with transaction.atomic():
            applicant = Applicant.objects.create(**applicant_data)

            # Related objects
            if "sponsor_visa" in data:
                SponsorVisa.objects.create(applicant=applicant, **data["sponsor_visa"])
            if "relative" in data:
                Relative.objects.create(applicant=applicant, **data["relative"])
            if "other_information" in data:
                OtherInformation.objects.create(applicant=applicant, **data["other_information"])
            if "skills_experience" in data:
                SkillsExperience.objects.create(applicant=applicant, **data["skills_experience"])
            print("Creating applicant with:", applicant_data)
            ApplicantSelection.objects.create(applicant=applicant, is_active=True, is_selected=False)
        
        return response("success", 201, "Applicant created", {"id": applicant.id})

    except Exception as e:
        return response("error", 400, "Bad request", {"error": str(e)})

# Update Applicant
@csrf_exempt
def update_applicant(request, applicant_id):
    if request.method != "PUT":
        return response("error", 405, "Only PUT allowed")

    try:
        applicant = Applicant.objects.filter(passport_no=applicant_id).first()
        if not applicant:
            return response("fail", 404, "Applicant not found")

        data = json.loads(request.body)

        with transaction.atomic():
            # ✅ Update Applicant base fields 
            if "applicant" in data:
                for key, value in data["applicant"].items():
                    setattr(applicant, key, value)
                applicant.save()

            # ✅ SponsorVisas (many-to-one)
            if "sponsor_visas" in data:
                for sponsor in data["sponsor_visas"]:
                    sponsor_id = sponsor.pop("id", None)
                    if sponsor_id:
                        SponsorVisa.objects.filter(id=sponsor_id, applicant=applicant).update(**sponsor)
                    else:
                        SponsorVisa.objects.create(applicant=applicant, **sponsor)

            # ✅ Relatives (many-to-one)
            if "relatives" in data:
                for relative in data["relatives"]:
                    relative_id = relative.pop("id", None)
                    if relative_id:
                        Relative.objects.filter(id=relative_id, applicant=applicant).update(**relative)
                    else:
                        Relative.objects.create(applicant=applicant, **relative)

            # ✅ OtherInformation (one-to-one)
            if "other_information" in data:
                other_info_data = data["other_information"]
                if hasattr(applicant, "other_information"):
                    for key, value in other_info_data.items():
                        setattr(applicant.other_information, key, value)
                    applicant.other_information.save()
                else:
                    OtherInformation.objects.create(applicant=applicant, **other_info_data)

            # ✅ SkillsExperience (one-to-one)
            if "skills_experience" in data:
                skills_data = data["skills_experience"]
                if hasattr(applicant, "skills_experience"):
                    for key, value in skills_data.items():
                        setattr(applicant.skills_experience, key, value)
                    applicant.skills_experience.save()
                else:
                    SkillsExperience.objects.create(applicant=applicant, **skills_data)

            # ✅ ApplicantSelection (one-to-one)
            if "applicant_selection" in data:
                selection_data = data["applicant_selection"]
                if hasattr(applicant, "selection_status"):
                    for key, value in selection_data.items():
                        setattr(applicant.selection_status, key, value)
                    applicant.selection_status.save()
                else:
                    ApplicantSelection.objects.create(applicant=applicant, **selection_data)

        return response("success", 200, "Applicant updated")

    except Exception as e:
        return response("error", 400, "Bad request", {"error": str(e)})

 
# Delete Applicant
@csrf_exempt
def delete_applicant(request, applicant_id):
    if request.method != "DELETE":
        return response("error", 405, "Only DELETE allowed")
    try:
        applicant = Applicant.objects.filter(id=applicant_id).first()
        if not applicant:
            return response("fail", 404, "Applicant not found")
        applicant.delete()
        return response("success", 200, "Applicant deleted")
    except Exception as e:
        return response("error", 400, "Bad request", {"error": str(e)})

def calculate_age_range(min_age, max_age):
    today = date.today()
    min_birth_date = None
    max_birth_date = None
    if min_age is not None:
        max_birth_date = date(today.year - int(min_age), today.month, today.day)
    if max_age is not None:
        min_birth_date = date(today.year - int(max_age) - 1, today.month, today.day)
    return min_birth_date, max_birth_date


def get_applicant_full_info(applicant, request=None):
    """Return serialized applicant info including base64 images."""
    def clean_dict(d):
        return {k: v for k, v in d.items() if not k.startswith('_') and k != 'applicant_id'}

    return {
        "id": applicant.id,
        "application_no": applicant.application_no,
        "selection_status": clean_dict(applicant.selection_status.__dict__) if hasattr(applicant, "selection_status") else None,
        "date": applicant.date.isoformat() if applicant.date else None,
        "full_name": applicant.full_name,
        "passport_no": applicant.passport_no,
        "passport_type": applicant.passport_type,
        "place_of_issue": applicant.place_of_issue,
        "place_of_birth": applicant.place_of_birth,
        "date_of_issue": applicant.date_of_issue.isoformat() if applicant.date_of_issue else None,
        "date_of_expiry": applicant.date_of_expiry.isoformat() if applicant.date_of_expiry else None,
        "date_of_birth": applicant.date_of_birth.isoformat() if applicant.date_of_birth else None,
        "phone_no": applicant.phone_no,
        "religion": applicant.religion,
        "gender": applicant.gender,
        "marital_status": applicant.marital_status,
        "occupation": applicant.occupation,
        "qualification": applicant.qualification,
        "region": applicant.region,
        "city": applicant.city,
        "subcity_zone": applicant.subcity_zone,
        "woreda": applicant.woreda,
        "house_no": applicant.house_no,

        # Base64 images
        "photo": applicant.photo,
        "full_photo": applicant.full_photo,
        "passport_photo": applicant.passport_photo,

        # Related objects
        "sponsor_visas": [clean_dict(s.__dict__) for s in applicant.sponsor_visas.all()],
        "relatives": [clean_dict(r.__dict__) for r in applicant.relatives.all()],
        "other_information": clean_dict(applicant.other_information.__dict__) if hasattr(applicant, 'other_information') else None,
        "skills_experience": clean_dict(applicant.skills_experience.__dict__) if hasattr(applicant, 'skills_experience') else None,
        
    }


def list_applicants_full(request):
    try:
        qs = Applicant.objects.all()

        # Search by passport_no (partial)
        passport_no = request.GET.get("passport_no")
        gender = request.GET.get("gender")
        religion = request.GET.get("religion")
        full_name = request.GET.get("full_name")
        application_no = request.GET.get("application_no")
        if passport_no:
            qs = qs.filter(passport_no__icontains=passport_no)
        if full_name:
            qs = qs.filter(full_name__icontains=full_name)
        if application_no:
            qs = qs.filter(application_no__icontains=application_no)
        if gender:
            qs = qs.filter(gender__iexact=gender)
        if religion:
            qs = qs.filter(religion__iexact=religion) 

        # Filter by age (min_age, max_age)
        min_age = request.GET.get("min_age")
        max_age = request.GET.get("max_age")
        if min_age or max_age:
            min_birth_date, max_birth_date = calculate_age_range(min_age, max_age)
            if min_birth_date:
                qs = qs.filter(date_of_birth__lte=min_birth_date)
            if max_birth_date:
                qs = qs.filter(date_of_birth__gte=max_birth_date)

        # Filter by experience abroad (boolean) from SkillsExperience
        exp_abroad = request.GET.get("experience_abroad")
        if exp_abroad is not None:
            if exp_abroad.lower() == "true":
                qs = qs.filter(skills_experience__experience_abroad=True)
            elif exp_abroad.lower() == "false":
                qs = qs.filter(skills_experience__experience_abroad=False)

        # Build response data
        data = [get_applicant_full_info(applicant, request=request) for applicant in qs]

        return JsonResponse({"status": "success", "code": 200, "message": "Applicants fetched", "data": data})

    except Exception as e:
        return JsonResponse({"status": "error", "code": 400, "message": "Bad request", "error": str(e)}, status=400)


@api_view(['GET'])
def active_inactive_applicants(request):
    # Active applicants
    active_qs = ApplicantSelection.objects.filter(is_active=True)
    active_serializer = ApplicantSelectionSerializer(active_qs, many=True)
    active_count = active_qs.count()

    # Inactive applicants
    inactive_qs = ApplicantSelection.objects.filter(is_active=False)
    inactive_serializer = ApplicantSelectionSerializer(inactive_qs, many=True)
    inactive_count = inactive_qs.count()

    return Response({
        "active_count": active_count,
        "active_list": active_serializer.data,
        "inactive_count": inactive_count,
        "inactive_list": inactive_serializer.data
    })
    
@api_view(['GET'])
def total_applicants_count(request):
    count = Applicant.objects.count()
    return Response({"total_applicants": count})
    
@api_view(['GET'])
def selected_applicants(request):
    selected_qs = ApplicantSelection.objects.filter(is_selected=True)
    serializer = ApplicantSelectionSerializer(selected_qs, many=True)
    count = selected_qs.count()
    return Response({
        "selected_count": count,
        "selected_list": serializer.data
    })

@api_view(['GET'])
def selected_by_user(request, user_id):
    selected_qs = ApplicantSelection.objects.filter(is_selected=True, selected_by__id=user_id)
    serializer = ApplicantSelectionSerializer(selected_qs, many=True)
    count = selected_qs.count()
    return Response({
        "user_id": user_id,
        "selected_count": count,
        "selected_list": serializer.data
    })
    

@api_view(['POST'])
def applicant_selection(request, applicant_id):
    user_id = request.data.get('user_id')
    if not user_id:
        return Response({"error": "user_id is required"}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    # Ensure applicant exists
    try:
        applicant = Applicant.objects.get(id=applicant_id)
    except Applicant.DoesNotExist:
        return Response({"error": "Applicant does not exist"}, status=404)

    # Get or create selection record
    selection, created = ApplicantSelection.objects.get_or_create(
        applicant=applicant,
        defaults={'is_active': True, 'is_selected': False}
    )

    # Case 1: Already selected by another user
    if selection.is_selected and selection.selected_by != user:
        if user.role == "admin":
            # Admin can only deselect (not reselect)
            selection.is_selected = False
            selection.selected_by = None
            selection.selected_on = None
            selection.save()
            return Response({
                "message": "Admin removed selection",
                "applicant_id": applicant_id,
                "is_selected": selection.is_selected,
                "selected_by": None,
                "selected_by_username": None,
                "selected_on": None
            })
        else:
            return Response({
                "error": "Applicant is already selected by another user",
                "selected_by": selection.selected_by.username
            }, status=400)

    # Case 2: Selected by the same user → toggle off
    if selection.is_selected and selection.selected_by == user:
        selection.is_selected = False
        selection.selected_by = None
        selection.selected_on = None
        message = "Selection removed"

    # Case 3: Not selected → user can select
    else:
        selection.is_selected = True
        selection.selected_by = user
        selection.selected_on = timezone.now()
        message = "Applicant selected"

    selection.save()

    return Response({
        "message": message,
        "applicant_id": applicant_id,
        "is_selected": selection.is_selected,
        "selected_by": selection.selected_by.id if selection.selected_by else None,
        "selected_by_username": selection.selected_by.username if selection.selected_by else None,
        "selected_on": selection.selected_on
    })

@api_view(['GET'])
def partners_list(request):
    partners = User.objects.filter(role="partner")  # or "partner" if you fix typo
    data = [
        {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
        for user in partners
    ]
    return Response({"count": partners.count(), "partners": data})

@api_view(['POST'])
def applicant_active(request, applicant_id):
    try:
        selection = ApplicantSelection.objects.get(applicant_id=applicant_id)
    except ApplicantSelection.DoesNotExist:
        return Response({"error": "ApplicantSelection not found"}, status=status.HTTP_404_NOT_FOUND)

    # Flip the active status
    selection.is_active = not selection.is_active
    selection.save()

    return Response({
        "message": "Applicant active status updated",
        "applicant_id": applicant_id,
        "is_active": selection.is_active
    }, status=status.HTTP_200_OK)