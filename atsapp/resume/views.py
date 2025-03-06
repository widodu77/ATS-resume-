from django.shortcuts import render
from .forms import ResumeUploadForm
from .resume_processor import score_resume

def home(request):
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume_file = form.cleaned_data['resume_file']
            result = score_resume(resume_file)
            return render(request, 'resume/result.html', {'result': result})
    else:
        form = ResumeUploadForm()
    return render(request, 'resume/home.html', {'form': form})