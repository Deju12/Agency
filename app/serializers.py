from rest_framework import serializers
from .models import Applicant, SponsorVisa, Relative, OtherInformation, SkillsExperience

class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicant
        fields = '__all__'


class SponsorVisaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SponsorVisa
        fields = '__all__'


class RelativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relative
        fields = '__all__'


class OtherInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherInformation
        fields = '__all__'


class SkillsExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillsExperience
        fields = '__all__'
