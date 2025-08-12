import django_filters
from datetime import date
from .models import Applicant, SkillsExperience

class ApplicantFilter(django_filters.FilterSet):
    religion = django_filters.CharFilter(field_name="religion", lookup_expr='iexact')
    passport_no = django_filters.CharFilter(field_name="passport_no", lookup_expr='icontains')
    full_name = django_filters.CharFilter(field_name="full_name", lookup_expr='icontains')
    age = django_filters.NumberFilter(method='filter_by_age')

    class Meta:
        model = Applicant
        fields = ['religion', 'passport_no', 'full_name']

    def filter_by_age(self, queryset, name, value):
        today = date.today()
        cutoff_year = today.year - value
        return queryset.filter(date_of_birth__year=cutoff_year)


class SkillsExperienceFilter(django_filters.FilterSet):
    experience_abroad = django_filters.BooleanFilter(field_name="experience_abroad")

    class Meta:
        model = SkillsExperience
        fields = ['experience_abroad']
