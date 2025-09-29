from django.urls import path
from . import views

urlpatterns = [
    # Student Group URLs
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/', views.my_groups, name='my_groups'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/members/', views.add_members, name='add_members'),
    path('groups/<int:group_id>/members/remove/<int:member_id>/', views.remove_member, name='remove_member'),
    path('groups/<int:group_id>/submit/', views.submit_project, name='submit_project'),
    path('groups/<int:group_id>/edit/', views.edit_group, name='edit_group'),
    path('groups/<int:group_id>/delete/', views.delete_group, name='delete_group'),

    path('groups/<int:group_id>/submit/<str:doc_type>/', views.submit_document, name='submit_document'),

    
    
    
    # Teacher Dashboard URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/students/', views.view_students, name='view_students'),
    path('teacher/groups/', views.view_all_groups, name='view_all_groups'),
    path('teacher/download/', views.download_student_data, name='download_student_data'),
    path('teacher/group/<int:group_id>/approve/', views.approve_group, name='approve_group'),
    path('teacher/group/<int:group_id>/assign-mentor/', views.assign_mentor, name='assign_mentor'),
    
    path('teacher/group/<int:group_id>/', views.teacher_group_view, name='teacher_group_view'),
    path('teacher/submissions/', views.teacher_all_submissions, name='teacher_all_submissions'),
    # File Download URLs
    # path('groups/<int:group_id>/submit/<str:doc_type>/', views.submit_document, name='submit_document'),

    # path('download/ppt/<int:submission_id>/', views.download_ppt, name='download_ppt'),
    # path('download/synopsis/<int:submission_id>/', views.download_synopsis, name='download_synopsis'),
    # path('download/srs/<int:submission_id>/', views.download_srs, name='download_srs'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('submission/download/<int:submission_id>/<str:file_type>/', views.download_submission, name='download_submission'),
    path('submission/delete/<int:submission_id>/<str:file_type>/', views.delete_submission, name='delete_submission'),


]