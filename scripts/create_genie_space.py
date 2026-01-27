"""Script to create a Genie space from a configuration file."""

import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.genie_space_client import create_genie_space_from_file, GenieSpaceClient

# Load environment variables
load_dotenv()


def main():
    """Main entry point for creating Genie space."""
    parser = argparse.ArgumentParser(
        description="Create a Databricks Genie space from a configuration file"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="output/genie_space_config.json",
        help="Path to the Genie space configuration JSON file",
    )
    parser.add_argument(
        "--databricks-host",
        type=str,
        default=None,
        help="Databricks host URL (defaults to DATABRICKS_HOST env var)",
    )
    parser.add_argument(
        "--databricks-token",
        type=str,
        default=None,
        help="Databricks token (defaults to DATABRICKS_TOKEN env var)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/genie_space_result.json",
        help="Path to save the creation result (space ID and URL)",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Databricks Genie Space Creator")
    print("=" * 80)
    print()
    
    # Validate config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"✗ Error: Configuration file not found: {config_path}")
        return 1
    
    print(f"Configuration file: {config_path}")
    print()
    
    try:
        # Create the Genie space
        result = create_genie_space_from_file(
            config_path=str(config_path),
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token
        )
        
        print()
        print("=" * 80)
        print("Genie Space Created Successfully!")
        print("=" * 80)
        print()
        print(f"Space ID: {result['space_id']}")
        print(f"Space URL: {result['space_url']}")
        print()
        print("You can now access your Genie space at the URL above.")
        print()
        
        # Save result to file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Result saved to: {output_path}")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 80)
        print("Error Creating Genie Space")
        print("=" * 80)
        print()
        print(f"✗ Error: {e}")
        print()
        
        # Print more details if available
        if hasattr(e, 'response'):
            try:
                error_detail = e.response.json()
                print("API Error Details:")
                print(json.dumps(error_detail, indent=2))
            except:
                print("API Response Text:")
                print(e.response.text)
        
        import traceback
        print()
        print("Full traceback:")
        traceback.print_exc()
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
