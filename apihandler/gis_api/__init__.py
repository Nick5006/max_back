from dotenv import load_dotenv
from apihandler.gis_api.collect import DataCollector
import os

load_dotenv()

data_collector = DataCollector(os.environ["DADATA_TOKEN"], os.environ["DADATA_SECRET_TOKEN"], os.environ["HOUSESCORE_KEY"])