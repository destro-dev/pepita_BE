from django.contrib import admin
from .models import Company, UnderwritingAssessment, ChecklistKind, UnderwritingChecklist

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('vat_number', 'legal_form', 'activity', 'city', 'country')
    search_fields = ('vat_number', 'activity', 'city')
    list_filter = ('legal_form', 'country', 'region')

@admin.register(UnderwritingAssessment)
class UnderwritingAssessmentAdmin(admin.ModelAdmin):
    list_display = ('company', 'underwriting_year', 'risk_score', 'win_probability')
    search_fields = ('company__vat_number', 'company__activity')
    list_filter = ('underwriting_year', 'risk_score')

@admin.register(ChecklistKind)
class ChecklistKindAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating')
    search_fields = ('name',)

@admin.register(UnderwritingChecklist)
class UnderwritingChecklistAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'kind', 'value', 'is_compliant', 'completed_by')
    search_fields = ('assessment__company__vat_number', 'kind__name', 'completed_by')
    list_filter = ('is_compliant', 'kind')
