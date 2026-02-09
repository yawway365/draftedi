from pprint import pprint
import os
import requests
from dotenv import load_dotenv

# Load .env
load_dotenv()

BASE_URL = os.getenv("DRAFTEDI_BASE_URL")
API_KEY = os.getenv("API_KEY")

if not BASE_URL or not API_KEY:
    raise RuntimeError("Missing DRAFTEDI_BASE_URL or DRAFTEDI_API_KEY in .env")

def view_transactions():

    url = f"{BASE_URL}/api/transactions"
    headers = {
        "x-api-key": API_KEY,
        'file_id': '1'
    }

    response = requests.get(url, headers=headers, timeout=30)

    print(f"HTTP {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        print("Non-JSON response:")
        print(response.text)
        return

    pprint(data)

if __name__ == "__main__":
    view_transactions()
