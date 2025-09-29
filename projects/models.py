from django.db import models
from accounts.models import User, StudentProfile, TeacherProfile

class ProjectGroup(models.Model):
    name = models.CharField(max_length=100)
    section = models.CharField(max_length=10)
    project_title = models.CharField(max_length=200)
    problem_statement = models.TextField()
    project_explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    mentor = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name

class GroupMember(models.Model):
    ROLE_CHOICES = [
        ('lead', 'Team Lead'),
        ('member1', 'Team Member 1'),
        ('member2', 'Team Member 2'),
        ('member3', 'Team Member 3'),
    ]
    
    group = models.ForeignKey(ProjectGroup, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    class Meta:
        unique_together = ('group', 'student')
    
    def __str__(self):
        return f"{self.student.full_name} - {self.get_role_display()}"


class ProjectSubmission(models.Model):
    group = models.OneToOneField(ProjectGroup, on_delete=models.CASCADE)
    ppt_file = models.FileField(upload_to='submissions/ppt/', null=True, blank=True)
    synopsis_report = models.FileField(upload_to='submissions/synopsis/', null=True, blank=True)
    github_link = models.URLField(null=True, blank=True)
    srs_report = models.FileField(upload_to='submissions/srs/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Submission for {self.group.name}"