from django.db import models

class User(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('pertner', 'Partner'),
    )

    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    forgot_key = models.CharField(max_length=128, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username
    


class Applicant(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    application_no = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    full_name = models.CharField(max_length=150,blank=False, null=False) 
    photo = models.ImageField(upload_to='applicants/photos/', blank=False, null=False)
    passport_no = models.CharField(max_length=50)
    passport_type = models.CharField(max_length=50)
    place_of_issue = models.CharField(max_length=100)
    place_of_birth = models.CharField(max_length=100)
    date_of_issue = models.DateField()
    date_of_expiry = models.DateField()
    date_of_birth = models.DateField()
    phone_no = models.CharField(max_length=20)
    religion = models.CharField(max_length=50)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=50)
    occupation = models.CharField(max_length=100)
    qualification = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    subcity_zone = models.CharField(max_length=100)
    woreda = models.CharField(max_length=100)
    house_no = models.CharField(max_length=50)

    def __str__(self):
        return self.full_name


class SponsorVisa(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='sponsor_visas')
    visa_no = models.CharField(max_length=50)
    sponsor_name = models.CharField(max_length=150)
    sponsor_phone = models.CharField(max_length=20)
    sponsor_address = models.CharField(max_length=255)
    sponsor_arabic = models.CharField(max_length=255, blank=True, null=True)
    sponsor_id = models.CharField(max_length=50)
    agent_no = models.CharField(max_length=100)
    email = models.EmailField()
    file_no = models.CharField(max_length=50)
    signed_on = models.DateField()
    biometric_id = models.CharField(max_length=50)
    contract_no = models.CharField(max_length=50)
    sticker_visa_no = models.CharField(max_length=50)
    current_nationality = models.CharField(max_length=100)
    labor_id = models.CharField(max_length=50)
    visa_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.visa_no} - {self.sponsor_name}"


class Relative(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='relatives')
    relative_name = models.CharField(max_length=150)
    relative_phone = models.CharField(max_length=20)
    relative_kinship = models.CharField(max_length=100)
    relative_region = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    subcity_zone = models.CharField(max_length=100)
    woreda = models.CharField(max_length=100)
    house_no = models.CharField(max_length=50)

    def __str__(self):
        return self.relative_name


class OtherInformation(models.Model):
    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name='other_information')
    contact_person = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=20)
    ccc_center_name = models.CharField(max_length=150)
    certificate_no = models.CharField(max_length=50)
    certified_date = models.DateField()
    medical_place = models.CharField(max_length=150)
    trip_photographs = models.BooleanField(default=False)
    id_card = models.BooleanField(default=False)
    relative_id_card = models.BooleanField(default=False)

    def __str__(self):
        return f"Other Info for {self.applicant.full_name}"


class SkillsExperience(models.Model):
    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name='skills_experience')
    english = models.CharField(max_length=50)
    arabic = models.CharField(max_length=50)
    experience_abroad = models.BooleanField(default=False)
    works_in = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    height = models.DecimalField(max_digits=5, decimal_places=2)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    reference_no = models.CharField(max_length=50)
    no_of_children = models.IntegerField(default=0)
    remarks = models.TextField(blank=True, null=True)

    ironing = models.BooleanField(default=False)
    sewing = models.BooleanField(default=False)
    baby_sitting = models.BooleanField(default=False)
    old_care = models.BooleanField(default=False)
    all_cooking = models.BooleanField(default=False)
    cleaning = models.BooleanField(default=False)
    washing = models.BooleanField(default=False)
    cooking = models.BooleanField(default=False)

    def __str__(self):
        return f"Skills for {self.applicant.full_name}"
    
class ApplicantSelection(models.Model):
    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name="selection_status")
    is_active = models.BooleanField(default=True)  # Whether the applicant is active
    is_selected = models.BooleanField(default=False)  # Whether the applicant is selected
    selected_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="selected_applicants"
    )  # Which user selected the applicant
    selected_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # When selected

    def __str__(self):
        status = "Selected" if self.is_selected else "Not Selected"
        return f"{self.applicant.full_name} - {status}"
