from django.urls import path, include
from home.views import TriggerReportView, GetReportView

urlpatterns = [
    
    path('report/', TriggerReportView.as_view()),
    path('getreport/', GetReportView.as_view()),
    
]