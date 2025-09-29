from django import forms
from .models import ProjectGroup, GroupMember, ProjectSubmission

class ProjectGroupForm(forms.ModelForm):
    class Meta:
        model = ProjectGroup
        fields = ['name', 'project_title', 'problem_statement', 'project_explanation']

class GroupMemberForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        section = kwargs.pop('section', None)
        super().__init__(*args, **kwargs)
        if section:
            self.fields['student'].queryset = self.fields['student'].queryset.filter(section=section)
    
    class Meta:
        model = GroupMember
        fields = ['student', 'role']

class ProjectSubmissionForm(forms.ModelForm):
    class Meta:
        model = ProjectSubmission
        fields = ['ppt_file', 'synopsis_report', 'github_link', 'srs_report']


# CHANGED HERE

from django import forms
from .models import ProjectSubmission

class PresentationSubmissionForm(forms.ModelForm):
    class Meta:
        model = ProjectSubmission
        fields = ['ppt_file']
        widgets = {
            'ppt_file': forms.FileInput(attrs={'accept': '.ppt,.pptx,.pdf'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ppt_file'].label = 'Presentation File'
        self.fields['ppt_file'].help_text = 'Upload your presentation (PPT, PPTX, or PDF)'

class ReportSubmissionForm(forms.ModelForm):
    report_type = forms.ChoiceField(
        choices=[('synopsis', 'Synopsis Report'), ('srs', 'SRS Report')],
        widget=forms.RadioSelect
    )
    
    class Meta:
        model = ProjectSubmission
        fields = ['synopsis_report', 'srs_report']
        widgets = {
            'synopsis_report': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx'}),
            'srs_report': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['synopsis_report'].label = 'Synopsis Report File'
        self.fields['synopsis_report'].help_text = 'Upload your synopsis report (PDF, DOC, or DOCX)'
        self.fields['srs_report'].label = 'SRS Report File'
        self.fields['srs_report'].help_text = 'Upload your SRS report (PDF, DOC, or DOCX)'


class GitHubSubmissionForm(forms.ModelForm):
    class Meta:
        model = ProjectSubmission
        fields = ['github_link']
        widgets = {
            'github_link': forms.URLInput(attrs={'placeholder': 'https://github.com/username/repository'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['github_link'].label = 'GitHub Repository URL'
        self.fields['github_link'].help_text = 'Enter the URL of your GitHub repository'
