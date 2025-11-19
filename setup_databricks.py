#!/usr/bin/env python3
"""
Interactive script to help set up Databricks tables for the chatbot
"""

import os
from pathlib import Path

def print_banner():
    print("=" * 70)
    print("  DATABRICKS SETUP FOR KNOWLEDGE BASE CHATBOT")
    print("  DG-Prefixed Tables for Conversation Analytics")
    print("=" * 70)
    print()

def check_setup_file():
    """Check if setup SQL file exists"""
    sql_file = Path("setup_databricks_tables.sql")
    if sql_file.exists():
        print(f"✓ Found setup script: {sql_file}")
        return True
    else:
        print(f"✗ Setup script not found: {sql_file}")
        return False

def check_export_package():
    """Check if there's an export package available"""
    export_dir = Path("databricks_package")
    if export_dir.exists():
        files = list(export_dir.glob("*.sql"))
        csv_files = list((export_dir / "csv_data").glob("*.csv")) if (export_dir / "csv_data").exists() else []
        print(f"✓ Found export package with {len(files)} SQL files and {len(csv_files)} CSV files")
        return True, len(csv_files)
    else:
        print("ℹ No export package found (run 'python main.py export-databricks' first)")
        return False, 0

def display_setup_options():
    """Display setup options to user"""
    print("\n📋 SETUP OPTIONS:")
    print("-" * 70)
    print()
    print("Option 1: QUICK SETUP (Recommended)")
    print("  • Copy setup_databricks_tables.sql to Databricks SQL Editor")
    print("  • Update catalog/schema if needed (lines 7-8)")
    print("  • Click 'Run All'")
    print("  • Takes ~2 minutes")
    print()
    print("Option 2: IMPORT WITH DATA")
    print("  • First, export conversation data:")
    print("    $ python main.py export-databricks")
    print("  • Run 01_create_tables.sql in Databricks")
    print("  • Import CSV files using Data Import wizard OR")
    print("  • Run 02_insert_data.sql")
    print()
    print("Option 3: MANUAL SETUP")
    print("  • Follow step-by-step guide in DATABRICKS_SETUP_GUIDE.md")
    print()

def display_sql_preview():
    """Show preview of setup SQL"""
    print("\n📄 SQL SETUP PREVIEW:")
    print("-" * 70)

    sql_file = Path("setup_databricks_tables.sql")
    if sql_file.exists():
        with open(sql_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:30]  # Show first 30 lines
            for i, line in enumerate(lines, 1):
                print(f"{i:3d} | {line.rstrip()}")
        print(f"... ({len(open(sql_file).readlines())} total lines)")
    print()

def display_table_info():
    """Display information about DG tables"""
    print("\n📊 TABLES TO BE CREATED:")
    print("-" * 70)
    print()
    print("1. DG_CONVERSATIONS")
    print("   • Main conversation records")
    print("   • Includes: queries, responses, timestamps, performance metrics")
    print("   • Indexes: session_id, timestamp, user_id")
    print()
    print("2. DG_CONVERSATION_SOURCES")
    print("   • Links conversations to source documents")
    print("   • Includes: file names, similarity scores, rankings")
    print("   • Indexes: conversation_id, file_name")
    print()
    print("3. DG_CONVERSATION_METRICS")
    print("   • Optimized for reporting and analytics")
    print("   • Includes: daily aggregations, performance data")
    print("   • Indexes: date, session_id")
    print()
    print("VIEWS:")
    print("   • DG_CONVERSATIONS_WITH_SOURCES - Joined view")
    print("   • DG_DAILY_METRICS - Daily summary statistics")
    print()

def generate_connection_template():
    """Generate .env template for Databricks connection"""
    print("\n🔐 DATABRICKS CONNECTION TEMPLATE:")
    print("-" * 70)

    template = """
# Add these to your .env file for direct Databricks connection

DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_TOKEN=dapi1234567890abcdef
DATABRICKS_CATALOG=main
DATABRICKS_SCHEMA=default

# How to get these values:
# 1. Server Hostname: Workspace URL (remove https://)
# 2. HTTP Path: SQL Warehouse -> Connection Details -> HTTP Path
# 3. Token: User Settings -> Access Tokens -> Generate New Token
# 4. Catalog/Schema: Where you want to create tables
"""
    print(template)

    # Offer to save
    save = input("\n💾 Save connection template to .env.databricks? (y/n): ").lower()
    if save == 'y':
        with open('.env.databricks', 'w') as f:
            f.write(template)
        print("✓ Saved to .env.databricks")
        print("  Copy values to .env when ready")

def display_next_steps():
    """Show next steps after setup"""
    print("\n🚀 NEXT STEPS AFTER TABLE CREATION:")
    print("-" * 70)
    print()
    print("1. Verify tables created:")
    print("   SHOW TABLES LIKE 'DG_%';")
    print()
    print("2. Check table structure:")
    print("   DESCRIBE EXTENDED DG_CONVERSATIONS;")
    print()
    print("3. Test with sample query:")
    print("   SELECT COUNT(*) FROM DG_CONVERSATIONS;")
    print()
    print("4. Import data (if available):")
    print("   • Use Data Import wizard for CSV files")
    print("   • Or run INSERT statements from export")
    print()
    print("5. Create your first dashboard:")
    print("   • Use pre-built queries from 03_reporting_queries.sql")
    print("   • Start with DG_DAILY_METRICS view")
    print()
    print("6. Set up maintenance jobs:")
    print("   • Weekly: OPTIMIZE and ANALYZE TABLE")
    print("   • Monthly: VACUUM old data")
    print()

def open_guide():
    """Offer to open the setup guide"""
    guide_file = Path("DATABRICKS_SETUP_GUIDE.md")
    if guide_file.exists():
        print(f"\n📖 Detailed guide available: {guide_file}")
        open_it = input("   Open guide in default viewer? (y/n): ").lower()
        if open_it == 'y':
            try:
                import webbrowser
                webbrowser.open(str(guide_file))
                print("✓ Guide opened")
            except:
                print("ℹ Please open manually:", guide_file)

def main():
    print_banner()

    # Check prerequisites
    print("🔍 CHECKING PREREQUISITES:")
    print("-" * 70)
    sql_exists = check_setup_file()
    export_exists, csv_count = check_export_package()

    if not sql_exists:
        print("\n❌ Setup files not found!")
        print("   Make sure you're in the correct directory")
        return

    print()

    # Display setup information
    display_setup_options()
    display_table_info()

    # Interactive menu
    while True:
        print("\n" + "=" * 70)
        print("WHAT WOULD YOU LIKE TO DO?")
        print("-" * 70)
        print("1. View SQL setup script preview")
        print("2. Show connection template for .env")
        print("3. View detailed setup guide")
        print("4. Export conversation data (if not done)")
        print("5. Show next steps after table creation")
        print("6. Exit")
        print()

        choice = input("Enter choice (1-6): ").strip()

        if choice == '1':
            display_sql_preview()
        elif choice == '2':
            generate_connection_template()
        elif choice == '3':
            open_guide()
        elif choice == '4':
            print("\n📤 Exporting conversation data...")
            try:
                from databricks_sync import create_databricks_sync_command
                create_databricks_sync_command()
            except Exception as e:
                print(f"❌ Export failed: {str(e)}")
        elif choice == '5':
            display_next_steps()
        elif choice == '6':
            break
        else:
            print("❌ Invalid choice")

    # Final summary
    print("\n" + "=" * 70)
    print("📋 SUMMARY - FILES READY FOR DATABRICKS:")
    print("-" * 70)
    print()
    print("✓ setup_databricks_tables.sql - Complete table creation script")
    print("✓ DATABRICKS_SETUP_GUIDE.md - Detailed setup documentation")

    if export_exists:
        print(f"✓ databricks_package/ - Export with {csv_count} CSV files")

    print()
    print("🎯 QUICK START:")
    print("1. Open Databricks SQL Editor")
    print("2. Copy/paste setup_databricks_tables.sql")
    print("3. Update catalog/schema (lines 7-8)")
    print("4. Run All")
    print()
    print("✅ Tables will be created with DG prefix for easy identification!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup assistant interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")