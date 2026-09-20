from django.contrib import admin

from .models import Guardian, Student


class GuardianInline(admin.TabularInline):
    model = Guardian
    extra = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["name", "school", "class_name"]
    list_filter = ["school", "class_name"]
    search_fields = ["name"]
    inlines = [GuardianInline]


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ["parent", "student", "relationship", "is_primary_contact"]
    list_filter = ["relationship", "is_primary_contact"]
