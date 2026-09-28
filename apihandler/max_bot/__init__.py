from pathlib import Path
import certifi
import ssl
import httpx

BASE_DIR = Path(__file__).resolve().parent.parent

CA_CERT = (Path(BASE_DIR) / ".." / "certs" / "Russian_Trusted_Root_CA.cer")
print(CA_CERT)
ssl_context = ssl.create_default_context(cafile = certifi.where())
ssl_context.load_verify_locations(cafile = str(CA_CERT))

client = httpx.Client(base_url = "https://platform-api2.max.ru", verify = ssl_context, timeout = 10)

