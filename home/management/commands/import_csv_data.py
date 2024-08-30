import os
import pandas as pd
from django.core.management.base import BaseCommand
from home.models import StoreStatus, BusinessHours, Timezone
from django.utils.timezone import make_aware
from datetime import datetime
from django.conf import settings
import pytz



class Command(BaseCommand):
    help = 'Import data from CSV files using Pandas'

    def handle(self, *args, **options):
        data_dir = os.path.join(settings.BASE_DIR, 'data')
        batch_size = 1000  # Batch size for bulk_create

        # Import StoreStatus data
        store_status_path = os.path.join(data_dir, 'store_status.csv')
        store_status_df = pd.read_csv(store_status_path)

        store_status_df['timestamp_utc'] = store_status_df['timestamp_utc'].str.replace(" UTC", "")
        store_status_df['timestamp_utc'] = pd.to_datetime(store_status_df['timestamp_utc'], format="%Y-%m-%d %H:%M:%S.%f", errors='coerce').fillna(
            pd.to_datetime(store_status_df['timestamp_utc'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
        )
        store_status_df['timestamp_utc'] = store_status_df['timestamp_utc'].apply(lambda x: make_aware(x, pytz.UTC))

        store_status_objects = [
            StoreStatus(
                store_id=row['store_id'],
                status=row['status'],
                timestamp_utc=row['timestamp_utc']
            ) for index, row in store_status_df.iterrows()
        ]
        StoreStatus.objects.bulk_create(store_status_objects, batch_size=batch_size)

        # Import BusinessHours data
        business_hours_path = os.path.join(data_dir, 'business_hours.csv')
        business_hours_df = pd.read_csv(business_hours_path)

        business_hours_objects = [
            BusinessHours(
                store_id=row['store_id'],
                day_of_week=row['day'],
                start_time_local=row['start_time_local'],
                end_time_local=row['end_time_local']
            ) for index, row in business_hours_df.iterrows()
        ]
        BusinessHours.objects.bulk_create(business_hours_objects, batch_size=batch_size)

        # Handle missing business hours by assuming 24/7 operation
        all_store_ids = set(StoreStatus.objects.values_list('store_id', flat=True))
        existing_business_hours_store_ids = set(BusinessHours.objects.values_list('store_id', flat=True))
        missing_business_hours_store_ids = all_store_ids - existing_business_hours_store_ids

        business_hours_defaults = [
            BusinessHours(
                store_id=store_id,
                day_of_week=day,
                start_time_local='00:00:00',
                end_time_local='23:59:59'
            ) for store_id in missing_business_hours_store_ids for day in range(7)
        ]
        BusinessHours.objects.bulk_create(business_hours_defaults, batch_size=batch_size)

        # Import Timezone data
        timezone_path = os.path.join(data_dir, 'timezones.csv')
        timezone_df = pd.read_csv(timezone_path)

        timezone_objects = [
            Timezone(
                store_id=row['store_id'],
                timezone_str=row['timezone_str']
            ) for index, row in timezone_df.iterrows()
        ]
        Timezone.objects.bulk_create(timezone_objects, batch_size=batch_size)

        # Handle missing timezones by assuming America/Chicago
        missing_timezone_store_ids = all_store_ids - set(Timezone.objects.values_list('store_id', flat=True))
        timezone_defaults = [
            Timezone(
                store_id=store_id,
                timezone_str='America/Chicago'
            ) for store_id in missing_timezone_store_ids
        ]
        Timezone.objects.bulk_create(timezone_defaults, batch_size=batch_size)

        self.stdout.write(self.style.SUCCESS('Successfully imported data using Pandas'))
