from dotenv import load_dotenv
from apihandler.gis_api.collect import DataCollector
import os

load_dotenv()

data_collector = DataCollector(os.getenv("DADATA_TOKEN"), os.getenv("DADATA_SECRET_TOKEN"))