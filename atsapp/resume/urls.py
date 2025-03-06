from django.urls import path
from .api_views import ResumeScoreAPIView
from . import views

app_name = 'resume'
urlpatterns = [
    path('api/score/', ResumeScoreAPIView.as_view(), name='resume-score'),
    path('', views.home, name='home'),
]