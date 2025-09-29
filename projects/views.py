from datetime import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse
from django.template.loader import render_to_string
from django.db.models import Q

import tempfile
import os

from project_portal import settings
from .models import ProjectGroup, GroupMember, ProjectSubmission
from .forms import GitHubSubmissionForm, PresentationSubmissionForm, ProjectGroupForm, GroupMemberForm, ProjectSubmissionForm, ReportSubmissionForm
from accounts.models import StudentProfile, TeacherProfile





@login_required
def create_group(request):
    if not request.user.is_student:
        return redirect('dashboard')
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('complete_student_profile')
    
    # Check if student is already in a group
    if GroupMember.objects.filter(student=student_profile).exists():
        messages.error(request, 'You are already a member of a group.')
        return redirect('my_groups')
    
    if request.method == 'POST':
        group_form = ProjectGroupForm(request.POST)
        if group_form.is_valid():
            group = group_form.save(commit=False)
            group.section = student_profile.section
            group.save()
            
            # Add the current user as team lead
            GroupMember.objects.create(
                group=group,
                student=student_profile,
                role='lead'
            )
            
            messages.success(request, 'Group created successfully! Now add members to your group.')
            return redirect('add_members', group_id=group.id)
    else:
        group_form = ProjectGroupForm()
    
    return render(request, 'projects/group_form.html', {'form': group_form})

@login_required
def my_groups(request):
    if not request.user.is_student:
        return redirect('dashboard')
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('complete_student_profile')
    
    groups = ProjectGroup.objects.filter(members__student=student_profile)
    
    return render(request, 'projects/my_groups.html', {
        'groups': groups
    })

@login_required
def add_members(request, group_id):
    if not request.user.is_student:
        return redirect('dashboard')
    
    group = get_object_or_404(ProjectGroup, id=group_id)
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('complete_student_profile')
    
    # Check if the current user is the team lead of this group
    if not GroupMember.objects.filter(group=group, student=student_profile, role='lead').exists():
        messages.error(request, 'You are not authorized to add members to this group.')
        return redirect('dashboard')
    
    # Get students from the same section excluding those already in a group
    # FIX: Use 'student__user_id' instead of 'student_id'
    existing_members = GroupMember.objects.filter(group__section=group.section).values_list('student__user_id', flat=True)
    
    available_students = StudentProfile.objects.filter(
        section=group.section
    ).exclude(
        user_id__in=existing_members  # FIX: Use user_id instead of id
    ).exclude(
        user=request.user  # Exclude current user (already added as lead)
    )
    
    if request.method == 'POST':
        member_form = GroupMemberForm(request.POST, section=group.section)
        if member_form.is_valid():
            member = member_form.save(commit=False)
            member.group = group
            
            # Check if student is already in a group
            if GroupMember.objects.filter(student=member.student).exists():
                messages.error(request, 'This student is already in a group.')
            else:
                member.save()
                messages.success(request, 'Member added successfully!')
                return redirect('add_members', group_id=group.id)
    else:
        member_form = GroupMemberForm(section=group.section)
        member_form.fields['student'].queryset = available_students
    
    # Get current members
    current_members = GroupMember.objects.filter(group=group)
    
    return render(request, 'projects/add_members.html', {
        'form': member_form,
        'group': group,
        'current_members': current_members,
        'max_members': 4 - current_members.count()  # Including lead
    })
@login_required
def remove_member(request, group_id, member_id):
    if not request.user.is_student:
        return redirect('dashboard')
    
    group = get_object_or_404(ProjectGroup, id=group_id)
    member = get_object_or_404(GroupMember, id=member_id, group=group)
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('complete_student_profile')
    
    # Check if the current user is the team lead of this group
    if not GroupMember.objects.filter(group=group, student=student_profile, role='lead').exists():
        messages.error(request, 'You are not authorized to remove members from this group.')
        return redirect('dashboard')
    
    # Cannot remove the team lead
    if member.role == 'lead':
        messages.error(request, 'Cannot remove the team lead from the group.')
        return redirect('add_members', group_id=group.id)
    
    member.delete()
    messages.success(request, 'Member removed successfully!')
    return redirect('add_members', group_id=group.id)
@login_required
def submit_project(request, group_id):
    if not request.user.is_student:
        return redirect('dashboard')
    
    group = get_object_or_404(ProjectGroup, id=group_id)
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('complete_student_profile')
    
    # Check if the current user is a member of this group
    if not GroupMember.objects.filter(group=group, student=student_profile).exists():
        messages.error(request, 'You are not authorized to submit for this group.')
        return redirect('dashboard')
    
    # Check if user is team lead
    is_team_lead = GroupMember.objects.filter(
        group=group, 
        student=student_profile, 
        role='lead'
    ).exists()
    
    if not is_team_lead:
        messages.error(request, 'Only team leads can submit project documents.')
        return redirect('group_detail', group_id=group.id)
    
    try:
        submission = ProjectSubmission.objects.get(group=group)
    except ProjectSubmission.DoesNotExist:
        submission = None
    
    if request.method == 'POST':
        # Handle form submission based on your current model
        ppt_file = request.FILES.get('ppt_file')
        synopsis_report = request.FILES.get('synopsis_report')
        srs_report = request.FILES.get('srs_report')
        github_link = request.POST.get('github_link')
        
        if submission:
            # Update existing submission
            if ppt_file:
                submission.ppt_file = ppt_file
            if synopsis_report:
                submission.synopsis_report = synopsis_report
            if srs_report:
                submission.srs_report = srs_report
            if github_link:
                submission.github_link = github_link
            submission.save()
        else:
            # Create new submission
            submission = ProjectSubmission.objects.create(
                group=group,
                ppt_file=ppt_file,
                synopsis_report=synopsis_report,
                srs_report=srs_report,
                github_link=github_link
            )
        
        messages.success(request, 'Project submitted successfully!')
        return redirect('group_detail', group_id=group.id)
    
    return render(request, 'projects/project_submission.html', {
        'group': group,
        'submission': submission
    })
@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher:
        return redirect('dashboard')
    
    try:
        teacher_profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('complete_teacher_profile')
    
    groups = ProjectGroup.objects.filter(mentor=teacher_profile)
    
    # Get all students for filtering
    all_students = StudentProfile.objects.all()
    sections = StudentProfile.objects.values_list('section', flat=True).distinct()
    branches = StudentProfile.objects.values_list('branch', flat=True).distinct()
    
    return render(request, 'projects/teacher_dashboard.html', {
        'groups': groups,
        'all_students': all_students,
        'sections': sections,
        'branches': branches
    })

@login_required
def view_students(request):
    if not request.user.is_teacher:
        return redirect('dashboard')
    
    students = StudentProfile.objects.all()
    sections = StudentProfile.objects.values_list('section', flat=True).distinct()
    branches = StudentProfile.objects.values_list('branch', flat=True).distinct()
    
    # Apply filters if provided
    section_filter = request.GET.get('section')
    branch_filter = request.GET.get('branch')
    search_query = request.GET.get('search')
    
    if section_filter:
        students = students.filter(section=section_filter)
    if branch_filter:
        students = students.filter(branch=branch_filter)
    if search_query:
        students = students.filter(
            Q(full_name__icontains=search_query) |
            Q(abc_id__icontains=search_query) |
            Q(email_id__icontains=search_query)
        )
    
    return render(request, 'projects/view_students.html', {
        'students': students,
        'sections': sections,
        'branches': branches,
        'current_section': section_filter,
        'current_branch': branch_filter,
        'search_query': search_query
    })

@login_required
def view_all_groups(request):
    if not request.user.is_teacher:
        return redirect('dashboard')
    
    groups = ProjectGroup.objects.all()
    sections = ProjectGroup.objects.values_list('section', flat=True).distinct()
    teachers = TeacherProfile.objects.all()
    
    # Apply filters if provided
    section_filter = request.GET.get('section')
    status_filter = request.GET.get('status')
    mentor_filter = request.GET.get('mentor')
    search_query = request.GET.get('search')
    
    if section_filter:
        groups = groups.filter(section=section_filter)
    if status_filter:
        if status_filter == 'approved':
            groups = groups.filter(is_approved=True)
        elif status_filter == 'pending':
            groups = groups.filter(is_approved=False)
    if mentor_filter:
        groups = groups.filter(mentor__id=mentor_filter)
    if search_query:
        groups = groups.filter(
            Q(name__icontains=search_query) |
            Q(project_title__icontains=search_query)
        )
    
    return render(request, 'projects/view_all_groups.html', {
        'groups': groups,
        'sections': sections,
        'teachers': teachers,
        'current_section': section_filter,
        'current_status': status_filter,
        'current_mentor': mentor_filter,
        'search_query': search_query
    })

# @login_required
# def group_detail(request, group_id):
#     group = get_object_or_404(ProjectGroup, id=group_id)
    
#     # Check if user has permission to view this group
#     if request.user.is_student:
#         try:
#             student_profile = StudentProfile.objects.get(user=request.user)
#             if not GroupMember.objects.filter(group=group, student=student_profile).exists():
#                 messages.error(request, 'You are not authorized to view this group.')
#                 return redirect('dashboard')
#         except StudentProfile.DoesNotExist:
#             messages.error(request, 'Please complete your profile first.')
#             return redirect('complete_student_profile')
    
#     members = GroupMember.objects.filter(group=group)
    
#     try:
#         submission = ProjectSubmission.objects.get(group=group)
#     except ProjectSubmission.DoesNotExist:
#         submission = None
    
#     return render(request, 'projects/group_detail.html', {
#         'group': group,
#         'members': members,
#         'submission': submission
#     })

# CHANGED HERE

# Add these utility functions at the top of projects/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ProjectGroup, ProjectSubmission, GroupMember, StudentProfile, TeacherProfile
from .forms import PresentationSubmissionForm, ReportSubmissionForm, GitHubSubmissionForm






@login_required
def teacher_group_view(request, group_id):
    """View for teachers to see group details and submissions"""
    if not request.user.is_teacher:
        return redirect('dashboard')
    
    group = get_object_or_404(ProjectGroup, id=group_id)
    
    members = GroupMember.objects.filter(group=group)
    submissions = ProjectSubmission.objects.filter(group=group)
    
    # Group submissions by type
    presentation_submissions = submissions.filter(submission_type='ppt').order_by('-submitted_at')
    synopsis_submissions = submissions.filter(submission_type='synopsis').order_by('-submitted_at')
    synopsis_submissions = submissions.filter(submission_type='srs').order_by('-submitted_at')
    github_links = submissions.filter(submission_type='github').order_by('-submitted_at')
    
    # Check if current teacher is the mentor
    is_mentor = False
    try:
        teacher_profile = TeacherProfile.objects.get(user=request.user)
        is_mentor = (group.mentor == teacher_profile)
    except TeacherProfile.DoesNotExist:
        pass
    
    return render(request, 'projects/teacher_group_detail.html', {
        'group': group,
        'members': members,
        'presentation_submissions': presentation_submissions,
        'synopsis_submissions': synopsis_submissions,
        'srs_submissions': srs_submissions,
        'github_links': github_links,
        'is_mentor': is_mentor
    })

@login_required
def teacher_all_submissions(request):
    """View for teachers to see all submissions across all groups"""
    if not request.user.is_teacher:
        return redirect('dashboard')
    
    # Get filter parameters
    section_filter = request.GET.get('section')
    submission_type_filter = request.GET.get('type')
    
    submissions = ProjectSubmission.objects.all().order_by('-submitted_at')
    
    # Apply filters
    if section_filter:
        submissions = submissions.filter(group__section=section_filter)
    if submission_type_filter:
        submissions = submissions.filter(submission_type=submission_type_filter)
    
    # Get unique sections and submission types for filter dropdowns
    sections = ProjectGroup.objects.values_list('section', flat=True).distinct()
    submission_types = ProjectSubmission.SUBMISSION_TYPES
    
    return render(request, 'projects/teacher_all_submissions.html', {
        'submissions': submissions,
        'sections': sections,
        'submission_types': submission_types,
        'current_section': section_filter,
        'current_type': submission_type_filter
    })



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse
from django.template.loader import render_to_string
from django.db.models import Q
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from io import BytesIO
import tempfile
import os
from .models import ProjectGroup, GroupMember, ProjectSubmission
from .forms import ProjectGroupForm, GroupMemberForm, ProjectSubmissionForm
from accounts.models import StudentProfile, TeacherProfile

# ... (other imports and views)

@login_required
def download_student_data(request):
    if not request.user.is_teacher:
        return redirect('dashboard')
    
    # Get filter parameters
    section = request.GET.get('section')
    branch = request.GET.get('branch')
    
    # Filter students
    students = StudentProfile.objects.all()
    if section:
        students = students.filter(section=section)
    if branch:
        students = students.filter(branch=branch)
    
    # Create a BytesIO buffer for the PDF
    buffer = BytesIO()
    
    # Create the PDF object
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Set up PDF content
    p.setFont("Helvetica-Bold", 16)
    p.drawString(1 * inch, height - 1 * inch, "Student Report")
    p.setFont("Helvetica", 10)
    
    y_position = height - 1.5 * inch
    p.drawString(1 * inch, y_position, "Generated on: {}".format(timezone.now().strftime("%Y-%m-%d %H:%M")))
    
    # Add table headers
    y_position -= 0.5 * inch
    p.setFont("Helvetica-Bold", 10)
    p.drawString(1 * inch, y_position, "Name")
    p.drawString(3 * inch, y_position, "ABC ID")
    p.drawString(4.5 * inch, y_position, "Section")
    p.drawString(5.5 * inch, y_position, "Branch")
    p.setFont("Helvetica", 10)
    
    # Add student data
    y_position -= 0.3 * inch
    for student in students:
        if y_position < 1 * inch:  # Check if we need a new page
            p.showPage()
            p.setFont("Helvetica", 10)
            y_position = height - 1 * inch
            
        p.drawString(1 * inch, y_position, student.full_name)
        p.drawString(3 * inch, y_position, student.abc_id)
        p.drawString(4.5 * inch, y_position, student.section)
        p.drawString(5.5 * inch, y_position, student.branch)
        y_position -= 0.3 * inch
    
    # Finish the PDF
    p.showPage()
    p.save()
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=student_report.pdf'
    return response

@login_required
def approve_group(request, group_id):
    if not request.user.is_teacher:
        return redirect('dashboard')
    
    group = get_object_or_404(ProjectGroup, id=group_id)
    
    try:
        teacher_profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('complete_teacher_profile')
    
    # Check if the teacher is the mentor of this group
    if group.mentor != teacher_profile:
        messages.error(request, 'You are not the mentor of this group.')
        return redirect('teacher_dashboard')
    
    group.is_approved = True
    group.save()
    messages.success(request, 'Group approved successfully!')
    return redirect('teacher_dashboard')

@login_required
def assign_mentor(request, group_id):
    if not request.user.is_teacher:
        return redirect('dashboard')
    
    group = get_object_or_404(ProjectGroup, id=group_id)
    
    if request.method == 'POST':
        mentor_id = request.POST.get('mentor')
        if mentor_id:
            try:
                mentor = TeacherProfile.objects.get(id=mentor_id)
                group.mentor = mentor
                group.save()
                messages.success(request, f'Mentor assigned successfully to {mentor.full_name}!')
            except TeacherProfile.DoesNotExist:
                messages.error(request, 'Invalid mentor selected.')
    
    return redirect('view_all_groups')

@login_required
def edit_group(request, group_id):
    if not request.user.is_student:
        return redirect('dashboard')
    
    group = get_object_or_404(ProjectGroup, id=group_id)
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('complete_student_profile')
    
    # Check if the current user is the team lead of this group
    if not GroupMember.objects.filter(group=group, student=student_profile, role='lead').exists():
        messages.error(request, 'You are not authorized to edit this group.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProjectGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Group updated successfully!')
            return redirect('group_detail', group_id=group.id)
    else:
        form = ProjectGroupForm(instance=group)
    
    return render(request, 'projects/group_form.html', {
        'form': form,
        'editing': True,
        'group': group
    })

@login_required
def delete_group(request, group_id):
    if not request.user.is_student:
        return redirect('dashboard')
    
    group = get_object_or_404(ProjectGroup, id=group_id)
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('complete_student_profile')
    
    # Check if the current user is the team lead of this group
    if not GroupMember.objects.filter(group=group, student=student_profile, role='lead').exists():
        messages.error(request, 'You are not authorized to delete this group.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Group deleted successfully!')
        return redirect('my_groups')
    
    return render(request, 'projects/delete_group.html', {
        'group': group
    })

# @login_required
# def download_ppt(request, submission_id):
#     submission = get_object_or_404(ProjectSubmission, id=submission_id)
    
#     # Check if user has permission to download
#     if request.user.is_student:
#         try:
#             student_profile = StudentProfile.objects.get(user=request.user)
#             if not GroupMember.objects.filter(group=submission.group, student=student_profile).exists():
#                 messages.error(request, 'You are not authorized to download this file.')
#                 return redirect('dashboard')
#         except StudentProfile.DoesNotExist:
#             messages.error(request, 'Please complete your profile first.')
#             return redirect('complete_student_profile')
    
#     if submission.ppt_file:
#         response = FileResponse(submission.ppt_file.open(), as_attachment=True)
#         response['Content-Disposition'] = f'attachment; filename="{os.path.basename(submission.ppt_file.name)}"'
#         return response
#     else:
#         messages.error(request, 'File not found.')
#         return redirect('group_detail', group_id=submission.group.id)

# @login_required
# def download_synopsis(request, submission_id):
#     submission = get_object_or_404(ProjectSubmission, id=submission_id)
    
#     # Check if user has permission to download
#     if request.user.is_student:
#         try:
#             student_profile = StudentProfile.objects.get(user=request.user)
#             if not GroupMember.objects.filter(group=submission.group, student=student_profile).exists():
#                 messages.error(request, 'You are not authorized to download this file.')
#                 return redirect('dashboard')
#         except StudentProfile.DoesNotExist:
#             messages.error(request, 'Please complete your profile first.')
#             return redirect('complete_student_profile')
    
#     if submission.synopsis_report:
#         response = FileResponse(submission.synopsis_report.open(), as_attachment=True)
#         response['Content-Disposition'] = f'attachment; filename="{os.path.basename(submission.synopsis_report.name)}"'
#         return response
#     else:
#         messages.error(request, 'File not found.')
#         return redirect('group_detail', group_id=submission.group.id)

# @login_required
# def download_srs(request, submission_id):
#     submission = get_object_or_404(ProjectSubmission, id=submission_id)
    
#     # Check if user has permission to download
#     if request.user.is_student:
#         try:
#             student_profile = StudentProfile.objects.get(user=request.user)
#             if not GroupMember.objects.filter(group=submission.group, student=student_profile).exists():
#                 messages.error(request, 'You are not authorized to download this file.')
#                 return redirect('dashboard')
#         except StudentProfile.DoesNotExist:
#             messages.error(request, 'Please complete your profile first.')
#             return redirect('complete_student_profile')
    
#     if submission.srs_report:
#         response = FileResponse(submission.srs_report.open(), as_attachment=True)
#         response['Content-Disposition'] = f'attachment; filename="{os.path.basename(submission.srs_report.name)}"'
#         return response
#     else:
#         messages.error(request, 'File not found.')
#         return redirect('group_detail', group_id=submission.group.id)

# Add these utility functions at the top of projects/views.py


# Update the group_detail view


# Update the submit_document view






def download_presentation(request, submission_id):
    submission = get_object_or_404(submission, id=submission_id)
    if not submission.ppt_file:
        raise Http404("No PPT file found")
    file_path = submission.ppt_file.path
    return download_file(file_path)

def download_synopsis(request, submission_id):
    submission = get_object_or_404(submission, id=submission_id)
    if not submission.synopsis_report:
        raise Http404("No Synopsis file found")
    file_path = submission.synopsis_report.path
    return download_file(file_path)

def download_srs(request, submission_id):
    submission = get_object_or_404(submission, id=submission_id)
    if not submission.srs_report:
        raise Http404("No SRS file found")
    file_path = submission.srs_report.path
    return download_file(file_path)

def download_github(request, submission_id):
    submission = get_object_or_404(submission, id=submission_id)
    if not submission.github_link:
        raise Http404("No GitHub link found")
    # For GitHub, maybe just redirect
    return redirect(submission.github_link)

# Helper

@login_required
def download_file(request, submission_id):
    submission = get_object_or_404(ProjectSubmission, id=submission_id)
    
    # Check if user has permission to download
    if not can_view_submissions(request.user, submission.group):
        messages.error(request, 'You are not authorized to download this file.')
        return redirect('dashboard')
    
    if submission.file:
        response = FileResponse(submission.file.open(), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(submission.file.name)}"'
        return response
    else:
        messages.error(request, 'File not found.')
        return redirect('group_detail', group_id=submission.group.id)


@login_required
def download_submission(request, submission_id, file_type):
    submission = get_object_or_404(submission, id=submission_id)
    file_field = None

    if file_type == 'ppt':
        file_field = submission.ppt_file
    elif file_type == 'synopsis':
        file_field = submission.synopsis_report
    elif file_type == 'srs':
        file_field = submission.srs_report
    else:
        raise Http404("File type not found")

    if not file_field:
        raise Http404("File not found")

    file_path = os.path.join(settings.MEDIA_ROOT, file_field.name)
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_field.name))


@login_required
def delete_submission(request, submission_id, file_type):
    submission = get_object_or_404(submission, id=submission_id)
    
    if request.method == 'POST':
        if file_type == 'ppt' and submission.ppt_file:
            submission.ppt_file.delete()
        elif file_type == 'synopsis' and submission.synopsis_report:
            submission.synopsis_report.delete()
        elif file_type == 'srs' and submission.srs_report:
            submission.srs_report.delete()
        elif file_type == 'github':
            submission.github_link = ''
            submission.save()
        else:
            raise Http404("File type not found")

        return redirect('group_detail', group_id=submission.group.id)

    return render(request, 'projects/confirm_delete.html', {'submission': submission, 'file_type': file_type})


# DEEPSEEK FINAL 

# Add these utility functions at the top of projects/views.py
def can_view_submissions(user, group):
    """Check if user can view submissions for a group"""
    if user.is_superuser:
        return True
    
    if user.is_teacher:
        # All teachers can view submissions
        return True
    
    if user.is_student:
        try:
            student_profile = StudentProfile.objects.get(user=user)
            # Team members can view submissions
            return GroupMember.objects.filter(group=group, student=student_profile).exists()
        except StudentProfile.DoesNotExist:
            return False
    
    return False

def can_edit_submissions(user, group):
    """Check if user can edit/submit documents for a group"""
    if user.is_superuser:
        return True
    
    if user.is_student:
        try:
            student_profile = StudentProfile.objects.get(user=user)
            # Only team leads can edit submissions
            return GroupMember.objects.filter(
                group=group, 
                student=student_profile, 
                role='lead'
            ).exists()
        except StudentProfile.DoesNotExist:
            return False
    
    return False

# Update the group_detail view
@login_required
def group_detail(request, group_id):
    group = get_object_or_404(ProjectGroup, id=group_id)
    
    if not can_view_submissions(request.user, group):
        messages.error(request, 'You are not authorized to view this group.')
        return redirect('dashboard')
    
    can_edit = can_edit_submissions(request.user, group)
    
    members = GroupMember.objects.filter(group=group)
    
    # Get submissions based on your current model structure
    try:
        submission = ProjectSubmission.objects.get(group=group)
        has_submission = True
    except ProjectSubmission.DoesNotExist:
        submission = None
        has_submission = False
    
    mentor = group.mentor
    
    return render(request, 'projects/group_detail.html', {
        'group': group,
        'members': members,
        'submission': submission,
        'has_submission': has_submission,
        'can_edit': can_edit,
        'mentor': mentor
    })
# Update the submit_document view
@login_required
def submit_document(request, group_id, doc_type):
    group = get_object_or_404(ProjectGroup, id=group_id)
    
    # Check if user has permission to submit documents
    if not can_edit_submissions(request.user, group):
        messages.error(request, 'Only team leads can submit documents.')
        return redirect('group_detail', group_id=group.id)
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('complete_student_profile')
    
    # Determine which form to use based on document type
    if doc_type == 'presentation':
        form_class = PresentationSubmissionForm
        submission_type = 'ppt'
    elif doc_type == 'report':
        form_class = ReportSubmissionForm
        submission_type = None
    elif doc_type == 'github':
        form_class = GitHubSubmissionForm
        submission_type = 'github'
    else:
        messages.error(request, 'Invalid document type.')
        return redirect('group_detail', group_id=group.id)
    
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.group = group
            submission.submitted_by = student_profile
            
            if doc_type == 'report':
                submission.submission_type = form.cleaned_data['report_type']
            else:
                submission.submission_type = submission_type
            
            submission.save()
            messages.success(request, f'{submission.get_submission_type_display()} submitted successfully!')
            return redirect('group_detail', group_id=group.id)
    else:
        form = form_class()
    
    # Get existing submissions of this type
    if doc_type == 'report':
        existing_submissions = ProjectSubmission.objects.filter(
            group=group, 
            submission_type__in=['synopsis', 'srs']
        ).order_by('-submitted_at')
    else:
        existing_submissions = ProjectSubmission.objects.filter(
            group=group, 
            submission_type=submission_type
        ).order_by('-submitted_at')
    
    return render(request, 'projects/submit_document.html', {
        'form': form,
        'group': group,
        'doc_type': doc_type,
        'existing_submissions': existing_submissions
    })