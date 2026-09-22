from dadata import Dadata
import httpx
import os

class DataCollector:
    def __init__(self, token: str, secret_token: str):
        self.dadata = Dadata(token, secret_token)

    def get_house_fias_id(self, address: str):
        return self.dadata.clean("address", address).get("house_fias_id")

    def get_house_management(self, address: str):
        fias_id = self.get_house_fias_id(address)

        if fias_id is None:
            return None

        try:
            response = httpx.get(f"https://housescore.ru/api/houses/{fias_id}/management", headers = {"Authorization": f"Bearer {os.getenv("HOUSESCORE_KEY")}"})
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as err:
            raise err
