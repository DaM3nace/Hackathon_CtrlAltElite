"""
Wrapper script to run migration with forced environment variables
"""
import os
import sys

# Force the correct environment variables before any imports
os.environ['DATABRICKS_CATALOG'] = 'hackathon'
os.environ['DATABRICKS_SCHEMA'] = 'hackathon_ctrl_alt_elite'

print("=" * 80)
print("MIGRATION WITH FORCED ENVIRONMENT VARIABLES")
print("=" * 80)
print()
print("Forcing environment variables:")
print(f"  DATABRICKS_CATALOG={os.environ['DATABRICKS_CATALOG']}")
print(f"  DATABRICKS_SCHEMA={os.environ['DATABRICKS_SCHEMA']}")
print()

# Now run the migration
print("Starting migration...")
print()

# Import and run the migration
from migrate_to_databricks import migrate_to_databricks

# Run migration
success = migrate_to_databricks()

if success:
    print()
    print("=" * 80)
    print("MIGRATION SUCCESSFUL!")
    print("=" * 80)
    print()
    print("Data migrated to:")
    print("  hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS")
    print("  hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS")
    print("  hackathon.hackathon_ctrl_alt_elite.DG_VECTORS")
    print()
    print("Next step: Restart chatbot")
    print("  python web_chat.py")
    print()
    sys.exit(0)
else:
    print()
    print("=" * 80)
    print("MIGRATION FAILED!")
    print("=" * 80)
    print()
    print("Check the error messages above for details.")
    print()
    sys.exit(1)
