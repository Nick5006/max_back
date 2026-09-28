from django.conf import settings
from apihandler.gis_api.collect import DataCollector

data_collector = DataCollector(settings.DADATA_TOKEN, settings.DADATA_SECRET_TOKEN, settings.HOUSESCORE_KEY)