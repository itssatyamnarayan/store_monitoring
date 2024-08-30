from django.db import models

class ReportStatus(models.Model):
    report_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20)  
