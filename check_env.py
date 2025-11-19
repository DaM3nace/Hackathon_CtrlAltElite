import os
print("DATABRICKS_CATALOG:", os.environ.get("DATABRICKS_CATALOG", "NOT SET"))
print("DATABRICKS_SCHEMA:", os.environ.get("DATABRICKS_SCHEMA", "NOT SET"))
