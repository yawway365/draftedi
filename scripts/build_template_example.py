"""
Test script to demonstrate building transaction set mapping templates.

Usage:
    python scripts/build_template_example.py 004010 810
"""

import sys
import json
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.build_mapping_template import (
    build_mapping_template,
    build_mandatory_only_template
)


def main():
    if len(sys.argv) != 3:
        print("Usage: python build_template_example.py <version> <transaction_set_id>")
        print("Example: python build_template_example.py 004010 810")
        sys.exit(1)
    
    version = sys.argv[1]
    transaction_set_id = sys.argv[2]
    
    print(f"Building template for {transaction_set_id} (version {version})...\n")
    
    # Build full template
    print("=" * 60)
    print("FULL TEMPLATE (all segments and elements)")
    print("=" * 60)
    full_template = build_mapping_template(version, transaction_set_id)
    print(json.dumps(full_template, indent=2))
    
    print("\n\n")
    
    # Build mandatory-only template
    print("=" * 60)
    print("MANDATORY ONLY TEMPLATE (minimal required fields)")
    print("=" * 60)
    mandatory_template = build_mandatory_only_template(version, transaction_set_id)
    print(json.dumps(mandatory_template, indent=2))
    
    # Save to files
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    full_path = output_dir / f"{transaction_set_id}_full_template.json"
    mandatory_path = output_dir / f"{transaction_set_id}_mandatory_template.json"
    
    with open(full_path, "w") as f:
        json.dump(full_template, f, indent=2)
    
    with open(mandatory_path, "w") as f:
        json.dump(mandatory_template, f, indent=2)
    
    print(f"\n\nTemplates saved to:")
    print(f"  - {full_path}")
    print(f"  - {mandatory_path}")


if __name__ == "__main__":
    main()