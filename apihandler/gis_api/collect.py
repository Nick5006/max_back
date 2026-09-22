from dadata import Dadata

class DataCollector:
    def __init__(self, token: str, secret_token: str):
        self.dadata = Dadata(token, secret_token)

    def get_house_fias_id(self, address: str):
        return self.dadata.clean("address", address).get("house_fias_id")
