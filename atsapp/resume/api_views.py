# resume/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .resume_processor import score_resume

class ResumeScoreAPIView(APIView):
    def post(self, request, format=None):
        resume_file = request.FILES.get("resume_file")
        if not resume_file:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        result = score_resume(resume_file)
        return Response(result)
