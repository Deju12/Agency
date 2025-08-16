from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from psycopg import Transaction
from .models import Applicant, OtherInformation, Relative, SkillsExperience, SponsorVisa, User
from django.db import connection, OperationalError
from django.db.models import Q
from datetime import date
from django.db import transaction

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
    
# Create Applicant  
@csrf_exempt
def create_applicant(request):
    if request.method != "POST":
        return response("error", 405, "Only POST allowed")
    try:
        data = json.loads(request.body)

        with transaction.atomic():
            # Extract only applicant fields here
            applicant_data = data.get("applicant", {})
            applicant = Applicant.objects.create(**applicant_data)

            # Create SponsorVisa
            sponsor_visa_data = data.get("sponsor_visa")
            if sponsor_visa_data:
                SponsorVisa.objects.create(applicant=applicant, **sponsor_visa_data)

            # Create Relative
            relative_data = data.get("relative")
            if relative_data:
                Relative.objects.create(applicant=applicant, **relative_data)

            # Create OtherInformation (OneToOne)
            other_info_data = data.get("other_information")
            if other_info_data:
                OtherInformation.objects.create(applicant=applicant, **other_info_data)

            # Create SkillsExperience (OneToOne)
            skills_data = data.get("skills_experience")
            if skills_data:
                SkillsExperience.objects.create(applicant=applicant, **skills_data)

        return response("success", 201, "Applicant created", {"id": applicant.id})
    except Exception as e:
        return response("error", 400, "Bad request", {"error": str(e)})

# Read All with Filters/Search
def list_applicants(request):
    try:
        qs = Applicant.objects.all()

        # Filtering
        religion = request.GET.get("religion")
        min_exp = request.GET.get("min_experience")
        max_exp = request.GET.get("max_experience")
        min_age = request.GET.get("min_age")
        max_age = request.GET.get("max_age")

        if religion:
            qs = qs.filter(religion__iexact=religion)
        if min_exp:
            qs = qs.filter(experience__gte=min_exp)
        if max_exp:
            qs = qs.filter(experience__lte=max_exp)
        if min_age:
            qs = qs.filter(age__gte=min_age)
        if max_age:
            qs = qs.filter(age__lte=max_age)

        # Search
        passport_id = request.GET.get("passport_id")
        applicant_name = request.GET.get("applicant_name")
        if passport_id:
            qs = qs.filter(passport_id__icontains=passport_id)
        if applicant_name:
            qs = qs.filter(name__icontains=applicant_name)

        data = list(qs.values())
        return response("success", 200, "Applicants fetched", data)
    except Exception as e:
        return response("error", 400, "Bad request", {"error": str(e)})

def get_applicant(request):
    try:
        # Allowed fields for filtering
        allowed_filters = ["application_no", "passport_no", "religion", "gender", "visa_no"]

        filters = {}
        for field in allowed_filters:
            value = request.GET.get(field)
            if value:
                filters[field] = value

        if not filters:
            return response("fail", 400, "No filter parameter provided")
         
        # Get only the first matching applicant
        applicant = Applicant.objects.filter(**filters).first()

        if not applicant:
            return response("fail", 404, "Applicant not found")

        # Serialize applicant fields
        applicant_data = {
            field.name: getattr(applicant, field.name)
            for field in applicant._meta.fields
        }

        return response("success", 200, "Applicant fetched", applicant_data)

    except Exception as e:
        return response("error", 400, "Bad request", {"error": str(e)})

# Update Applicant
@csrf_exempt
def update_applicant(request, applicant_id):
    if request.method != "PUT":
        return response("error", 405, "Only PUT allowed")
    try:
        applicant = Applicant.objects.filter(id=applicant_id).first()
        if not applicant:
            return response("fail", 404, "Applicant not found")
        data = json.loads(request.body)
        for key, value in data.items():
            setattr(applicant, key, value)
        applicant.save()
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
    
    
    
    
@csrf_exempt
def create_full_applicant(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "code": 405, "message": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)

        with Transaction.atomic():
            # Create Applicant first
            applicant_data = data.get("applicant")
            applicant = Applicant.objects.create(**applicant_data)

            # SponsorVisa (many-to-one)
            sponsor_visa_data = data.get("sponsor_visa")
            if sponsor_visa_data:
                SponsorVisa.objects.create(applicant=applicant, **sponsor_visa_data)

            # Relative (many-to-one)
            relative_data = data.get("relative")
            if relative_data:
                Relative.objects.create(applicant=applicant, **relative_data)

            # OtherInformation (one-to-one)
            other_info_data = data.get("other_information")
            if other_info_data:
                OtherInformation.objects.create(applicant=applicant, **other_info_data)

            # SkillsExperience (one-to-one)
            skills_data = data.get("skills_experience")
            if skills_data:
                SkillsExperience.objects.create(applicant=applicant, **skills_data)

        return JsonResponse({"status": "success", "code": 201, "message": "Applicant and related data created", "applicant_id": applicant.id})

    except Exception as e:
        return JsonResponse({"status": "error", "code": 400, "message": "Bad request", "error": str(e)}, status=400)


def calculate_age_range(min_age, max_age):
    today = date.today()
    min_birth_date = None
    max_birth_date = None
    if min_age is not None:
        max_birth_date = date(today.year - int(min_age), today.month, today.day)
    if max_age is not None:
        min_birth_date = date(today.year - int(max_age) - 1, today.month, today.day)
    return min_birth_date, max_birth_date


def get_applicant_full_info(applicant):
    # Convert related objects to dict excluding Django internal fields
    def clean_dict(d):
        return {k: v for k, v in d.items() if not k.startswith('_') and k != 'applicant_id'}

    return {
        "id": applicant.id,
        "application_no": applicant.application_no,
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

        "sponsor_visas": [clean_dict(sponsor_visa.__dict__) for sponsor_visa in applicant.sponsor_visas.all()],
        "relatives": [clean_dict(relative.__dict__) for relative in applicant.relatives.all()],
        "other_information": clean_dict(applicant.other_information.__dict__) if hasattr(applicant, 'other_information') else None,
        "skills_experience": clean_dict(applicant.skills_experience.__dict__) if hasattr(applicant, 'skills_experience') else None,
    }


def list_applicants_full(request):
    try:
        qs = Applicant.objects.all()

        # Search by passport_no (partial)
        passport_no = request.GET.get("passport_no")
        if passport_no:
            qs = qs.filter(passport_no__icontains=passport_no)

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
        data = [get_applicant_full_info(applicant) for applicant in qs]

        return JsonResponse({"status": "success", "code": 200, "message": "Applicants fetched", "data": data})

    except Exception as e:
        return JsonResponse({"status": "error", "code": 400, "message": "Bad request", "error": str(e)}, status=400)
