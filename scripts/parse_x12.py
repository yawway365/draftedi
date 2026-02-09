import os
import sys
import requests
from dotenv import load_dotenv
from pathlib import Path
from pprint import pprint

# Load .env
load_dotenv()

BASE_URL = os.getenv("DRAFTEDI_BASE_URL")
API_KEY = os.getenv("API_KEY")

if not BASE_URL or not API_KEY:
    raise RuntimeError("Missing DRAFTEDI_BASE_URL or DRAFTEDI_API_KEY in .env")

def parse_x12(file_path: str) -> None:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    url = f"{BASE_URL}/api/x12/parse"
    headers = {
        "x-api-key": API_KEY,
    }

    with path.open("rb") as f:
        files = {
            "file": (path.name, f, "application/octet-stream")
        }
        response = requests.post(url, headers=headers, files=files, timeout=30)

    print(f"HTTP {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        print("Non-JSON response:")
        print(response.text)
        return

    pprint(data)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parse_x12.py path/to/file.edi")
        sys.exit(1)

    parse_x12(sys.argv[1])
    # py scripts/parse_x12.py 'C:\Dev\simple_edi\sample.edi'
