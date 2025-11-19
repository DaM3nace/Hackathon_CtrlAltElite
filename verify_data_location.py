"""
Verify where the data actually is in Databricks
"""
import os
from databricks_storage import DatabricksStorage
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("VERIFYING DATA LOCATION IN DATABRICKS")
print("=" * 80)
print()

# Try location 1: hackathon.hackathon_ctrl_alt_elite (DESIRED)
print("Trying location 1: hackathon.hackathon_ctrl_alt_elite")
os.environ['DATABRICKS_CATALOG'] = 'hackathon'
os.environ['DATABRICKS_SCHEMA'] = 'hackathon_ctrl_alt_elite'
storage1 = DatabricksStorage()
count1 = storage1.get_document_count()
print(f"  Documents: {count1}")
print()

# Try location 2: hackathon_ctrl_alt_elite.documents (WHERE IT ACTUALLY WENT)
print("Trying location 2: hackathon_ctrl_alt_elite.documents")
os.environ['DATABRICKS_CATALOG'] = 'hackathon_ctrl_alt_elite'
os.environ['DATABRICKS_SCHEMA'] = 'documents'
storage2 = DatabricksStorage()
count2 = storage2.get_document_count()
print(f"  Documents: {count2}")
print()

print("=" * 80)
if count1 > 0:
    print(f"DATA FOUND AT: hackathon.hackathon_ctrl_alt_elite ({count1} documents)")
elif count2 > 0:
    print(f"DATA FOUND AT: hackathon_ctrl_alt_elite.documents ({count2} documents)")
else:
    print("NO DATA FOUND AT EITHER LOCATION!")
print("=" * 80)
