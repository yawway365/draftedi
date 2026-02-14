"""
Client script to fetch transaction set templates via API.

Usage:
    python scripts/fetch_template_from_api.py 004010 810
    python scripts/fetch_template_from_api.py 004010 810 --mandatory-only
"""

import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("DRAFTEDI_BASE_URL")
API_KEY = os.getenv("API_KEY")

if not BASE_URL or not API_KEY:
    raise RuntimeError("Missing DRAFTEDI_BASE_URL or API_KEY in .env")


def fetch_template(version: str, transaction_set_id: str, mandatory_only: bool = False):
    """Fetch template from the API"""
    url = f"{BASE_URL}/api/transaction-sets/{version}/{transaction_set_id}/template"
    
    headers = {
        "x-api-key": API_KEY,  
    }
    
    params = {
        "mandatory_only": mandatory_only
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f"Error: HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    return response.json()


def main():
    if len(sys.argv) < 3:
        print("Usage: python fetch_template_from_api.py <version> <transaction_set_id> [--mandatory-only]")
        print("Example: python fetch_template_from_api.py 004010 810")
        print("Example: python fetch_template_from_api.py 004010 810 --mandatory-only")
        sys.exit(1)
    
    version = sys.argv[1]
    transaction_set_id = sys.argv[2]
    mandatory_only = "--mandatory-only" in sys.argv
    
    print(f"Fetching template for {transaction_set_id} (version {version})...")
    if mandatory_only:
        print("(Mandatory fields only)")
    print()
    
    # Fetch from API
    result = fetch_template(version, transaction_set_id, mandatory_only)
    template = result.get("template")
    
    # Display
    print("=" * 60)
    print(f"TEMPLATE for {transaction_set_id}")
    print("=" * 60)
    print(json.dumps(template, indent=2))
    
    # Save to file
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    suffix = "_mandatory" if mandatory_only else "_full"
    output_path = output_dir / f"{transaction_set_id}{suffix}_template.json"
    
    with open(output_path, "w") as f:
        json.dump(template, f, indent=2)
    
    print(f"\n\nTemplate saved to: {output_path}")


if __name__ == "__main__":
    main()


