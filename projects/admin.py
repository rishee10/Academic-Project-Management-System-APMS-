from django.contrib import admin
from .models import ProjectGroup, GroupMember, ProjectSubmission

@admin.register(ProjectGroup)
class ProjectGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'section', 'project_title', 'mentor', 'is_approved']
    list_filter = ['section', 'is_approved']
    search_fields = ['name', 'project_title']
    actions = ['approve_groups']

    def approve_groups(self, request, queryset):
        queryset.update(is_approved=True)
    approve_groups.short_description = "Approve selected groups"

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['group', 'student', 'role']
    list_filter = ['group__section', 'role']

@admin.register(ProjectSubmission)
class ProjectSubmissionAdmin(admin.ModelAdmin):
    list_display = ['group', 'submitted_at']
    readonly_fields = ['submitted_at', 'updated_at']