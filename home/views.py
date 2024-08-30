from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from .logic import generate_report, greport_task
import uuid
import os
from threading import Thread
from rest_framework import status
from .reportstatus import ReportStatus


# TriggerReportView
class TriggerReportView(APIView):
    def get(self, request):
        report_id = str(uuid.uuid4())
        ReportStatus.objects.create(report_id=report_id, status='Running')
        
        
        def generate_report_task():

            greport_task(report_id)
            
        
        Thread(target=generate_report_task).start()
        return Response({'report_id': report_id}, status=status.HTTP_200_OK)

# GetReportView
class GetReportView(APIView):
    def get(self, request):
        report_id = request.GET.get('report_id')
        
        try:
            report_status = ReportStatus.objects.get(report_id=report_id)
        except ReportStatus.DoesNotExist:
            return Response({'status': 'Invalid report ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        report_filename = f'report_{report_id}.csv'
        
        if report_status.status == 'Completed' and os.path.exists(report_filename):
            with open(report_filename, 'rb') as f:
                response = HttpResponse(f.read(), content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{report_filename}"'
                return response
        else:
            return Response({'status': report_status.status}, status=status.HTTP_200_OK)

