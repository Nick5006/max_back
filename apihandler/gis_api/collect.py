from dadata import Dadata
import httpx

class DataCollector:
    def __init__(self, dadata_token: str, dadata_secret_token: str, housescore_token: str):
        self.dadata = Dadata(dadata_token, dadata_secret_token)
        self.housescore_token = housescore_token

    def get_house_fias_id(self, address: str):
        return self.dadata.clean("address", address).get("house_fias_id")

    def get_house_management(self, address: str):
        fias_id = self.get_house_fias_id(address)

        if fias_id is None:
            return None

        try:
            response = httpx.get(f"https://housescore.ru/api/houses/{fias_id}/management", headers = {"Authorization": f"Bearer {self.housescore_token}"})
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as err:
            raise err

    def get_houses(self, page_size: int = 10, page: int = 1):
        response = httpx.get(f"https://housescore.ru/api/houses", headers = {"Authorization": f"Bearer {self.housescore_token}"}, params = {"page_size": page_size, "page": page}, timeout = 10.0)
        response.raise_for_status()

        return response.json()
