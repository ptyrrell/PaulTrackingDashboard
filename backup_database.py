#!/usr/bin/env python
"""
Database Backup Script for Heroku PostgreSQL
This script creates local backups of your Heroku database
"""
import os
import subprocess
import datetime
import json

def create_backup():
    """Create a local backup of Heroku database"""
    
    # Create backups directory if it doesn't exist
    backup_dir = "database_backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("🔄 Creating Heroku database backup...")
    
    # Create backup on Heroku
    subprocess.run(["heroku", "pg:backups:capture"], check=True)
    
    print("📥 Downloading backup...")
    
    # Download the backup
    backup_file = f"{backup_dir}/backup_{timestamp}.dump"
    subprocess.run(["heroku", "pg:backups:download", "--output", backup_file], check=True)
    
    # Also export as SQL for readability
    print("📝 Exporting as SQL...")
    sql_file = f"{backup_dir}/backup_{timestamp}.sql"
    
    # Get database URL
    result = subprocess.run(["heroku", "config:get", "DATABASE_URL"], 
                          capture_output=True, text=True, check=True)
    db_url = result.stdout.strip()
    
    # Export to SQL using pg_dump (requires PostgreSQL client tools)
    try:
        subprocess.run(["pg_dump", db_url, "-f", sql_file, "--no-owner", "--no-acl"], 
                      check=True)
        print(f"✅ SQL backup created: {sql_file}")
    except:
        print("⚠️  Could not create SQL backup (pg_dump not available)")
    
    # Create metadata file
    metadata = {
        "timestamp": timestamp,
        "date": datetime.datetime.now().isoformat(),
        "backup_file": backup_file,
        "sql_file": sql_file if os.path.exists(sql_file) else None,
        "app_name": "paul-tracking-dashboard"
    }
    
    metadata_file = f"{backup_dir}/backup_{timestamp}_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Backup completed successfully!")
    print(f"📁 Files saved in: {backup_dir}/")
    print(f"   - Database dump: {backup_file}")
    if os.path.exists(sql_file):
        print(f"   - SQL export: {sql_file}")
    print(f"   - Metadata: {metadata_file}")
    
    # Show backup size
    size = os.path.getsize(backup_file) / (1024 * 1024)  # Convert to MB
    print(f"📊 Backup size: {size:.2f} MB")
    
    # List recent backups
    print("\n📚 Recent backups:")
    backups = sorted([f for f in os.listdir(backup_dir) if f.endswith('.dump')])[-5:]
    for backup in backups:
        print(f"   - {backup}")

def restore_backup(backup_file):
    """Restore a backup to Heroku database"""
    
    print(f"⚠️  WARNING: This will replace all data in the production database!")
    confirm = input("Type 'yes' to continue: ")
    
    if confirm.lower() != 'yes':
        print("❌ Restore cancelled")
        return
    
    print(f"📤 Uploading {backup_file} to restore...")
    # This would need to be implemented based on your restore strategy
    # For Heroku, you typically restore from Heroku's backup system
    print("ℹ️  To restore, use: heroku pg:backups:restore <backup_url> DATABASE_URL")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        if len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            print("Usage: python backup_database.py restore <backup_file>")
    else:
        create_backup()
