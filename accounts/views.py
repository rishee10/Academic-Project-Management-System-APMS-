from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserRegistrationForm, StudentProfileForm, TeacherProfileForm
from .models import StudentProfile, TeacherProfile
from projects.models import ProjectGroup, GroupMember

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Redirect to profile completion based on user type
            if user.is_student:
                return redirect('complete_student_profile')
            elif user.is_teacher:
                return redirect('complete_teacher_profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    has_profile = False
    groups = None
    
    if request.user.is_student:
        try:
            profile = StudentProfile.objects.get(user=request.user)
            has_profile = True
            groups = ProjectGroup.objects.filter(members__student=profile)
        except StudentProfile.DoesNotExist:
            pass
    elif request.user.is_teacher:
        try:
            profile = TeacherProfile.objects.get(user=request.user)
            has_profile = True
            groups = ProjectGroup.objects.filter(mentor=profile)
        except TeacherProfile.DoesNotExist:
            pass
    
    return render(request, 'dashboard.html', {
        'has_profile': has_profile,
        'groups': groups
    })

@login_required
def complete_student_profile(request):
    if not request.user.is_student:
        return redirect('dashboard')
    
    try:
        # Check if profile already exists
        StudentProfile.objects.get(user=request.user)
        messages.info(request, 'Your profile is already completed.')
        return redirect('profile')
    except StudentProfile.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile completed successfully!')
            return redirect('dashboard')
    else:
        form = StudentProfileForm()
    return render(request, 'accounts/profile_form.html', {'form': form, 'user_type': 'student'})

@login_required
def complete_teacher_profile(request):
    if not request.user.is_teacher:
        return redirect('dashboard')
    
    try:
        # Check if profile already exists
        TeacherProfile.objects.get(user=request.user)
        messages.info(request, 'Your profile is already completed.')
        return redirect('profile')
    except TeacherProfile.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = TeacherProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile completed successfully!')
            return redirect('dashboard')
    else:
        form = TeacherProfileForm()
    return render(request, 'accounts/profile_form.html', {'form': form, 'user_type': 'teacher'})

@login_required
def profile(request):
    try:
        if request.user.is_student:
            profile = StudentProfile.objects.get(user=request.user)
            groups = ProjectGroup.objects.filter(members__student=profile)
        elif request.user.is_teacher:
            profile = TeacherProfile.objects.get(user=request.user)
            groups = ProjectGroup.objects.filter(mentor=profile)
        else:
            profile = None
            groups = None
    except (StudentProfile.DoesNotExist, TeacherProfile.DoesNotExist):
        if request.user.is_student:
            return redirect('complete_student_profile')
        elif request.user.is_teacher:
            return redirect('complete_teacher_profile')
        else:
            return redirect('dashboard')
    
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'groups': groups
    })

@login_required
def edit_profile(request):
    try:
        if request.user.is_student:
            profile = StudentProfile.objects.get(user=request.user)
            if request.method == 'POST':
                form = StudentProfileForm(request.POST, request.FILES, instance=profile)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('profile')
            else:
                form = StudentProfileForm(instance=profile)
            user_type = 'student'
                
        elif request.user.is_teacher:
            profile = TeacherProfile.objects.get(user=request.user)
            if request.method == 'POST':
                form = TeacherProfileForm(request.POST, instance=profile)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('profile')
            else:
                form = TeacherProfileForm(instance=profile)
            user_type = 'teacher'
        else:
            return redirect('dashboard')
    except (StudentProfile.DoesNotExist, TeacherProfile.DoesNotExist):
        if request.user.is_student:
            return redirect('complete_student_profile')
        elif request.user.is_teacher:
            return redirect('complete_teacher_profile')
        else:
            return redirect('dashboard')
    
    return render(request, 'accounts/profile_form.html', {
        'form': form, 
        'user_type': user_type,
        'editing': True
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {
        'form': form
    })