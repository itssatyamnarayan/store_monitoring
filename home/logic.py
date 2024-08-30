import pytz
from datetime import timedelta
from .models import StoreStatus, Timezone, BusinessHours
import csv
from django.utils import timezone
from .reportstatus import ReportStatus

def convert_to_local_time(timestamp_utc, timezone_str):
    utc_time = timestamp_utc.replace(tzinfo=pytz.UTC)
    local_timezone = pytz.timezone(timezone_str)
    return utc_time.astimezone(local_timezone)

def compute_uptime_downtime(store_id, start_time, end_time):
    statuses = StoreStatus.objects.filter(
        store_id=store_id, timestamp_utc__range=(start_time, end_time)
    ).order_by('timestamp_utc')
    
    if not statuses.exists():
        return {'uptime': 0, 'downtime': 0}
    
    uptime = timedelta()
    downtime = timedelta()
    
    for i in range(len(statuses) - 1):
        current_status = statuses[i]
        next_status = statuses[i + 1]
        time_diff = next_status.timestamp_utc - current_status.timestamp_utc
        
        if current_status.status == 'active':
            uptime += time_diff
        else:
            downtime += time_diff

    return {
        'uptime': uptime.total_seconds() / 3600,  # Convert to hours
        'downtime': downtime.total_seconds() / 3600  # Convert to hours
    }

def generate_report(report_filename):
    report_data = []
   

    # Get all unique store IDs
    store_ids = StoreStatus.objects.values_list('store_id', flat=True).distinct()
   

    for store_id in store_ids:
      
        try:
           
            timezone_str = Timezone.objects.get(store_id=store_id).timezone_str
        
        except Timezone.DoesNotExist:
            timezone_str = 'America/Chicago'

        now = timezone.now().astimezone(pytz.timezone(timezone_str))
        
        # Calculate the time intervals
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        last_week = now - timedelta(weeks=1)
        
        # Compute uptime and downtime
        hour_data = compute_uptime_downtime(store_id, last_hour, now)
        day_data = compute_uptime_downtime(store_id, last_day, now)
        week_data = compute_uptime_downtime(store_id, last_week, now)
        
        report_data.append({
            'store_id': store_id,
            'uptime_last_hour': hour_data['uptime'] * 60,  # Convert to minutes
            'uptime_last_day': day_data['uptime'],
            'uptime_last_week': week_data['uptime'],
            'downtime_last_hour': hour_data['downtime'] * 60,  # Convert to minutes
            'downtime_last_day': day_data['downtime'],
            'downtime_last_week': week_data['downtime']
        })
        
    
    try:
        # Open the CSV file
        with open(report_filename, 'w', newline='') as csvfile:
            
            fieldnames = [
                'store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week',
                'downtime_last_hour', 'downtime_last_day', 'downtime_last_week'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
           
            writer.writeheader()
            
            
            writer.writerows(report_data)
            
        print(f'Report {report_filename} generated successfully.')
    except Exception as e:
       
        print(f'Error generating report: {e}')
        raise e  

    return report_filename

def greport_task(report_id):
    report_filename = f'report_{report_id}.csv'
    print(report_filename)
    try:
        generate_report(report_filename)
        ReportStatus.objects.filter(report_id=report_id).update(status='Completed')
    except Exception as e:
        ReportStatus.objects.filter(report_id=report_id).update(status='Failed')


    return report_id
        

