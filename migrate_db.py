import sqlite3
import os

DB_FILES = ["database.db", "instance/database.db", "instance/telemedicine.db"]

def add_check_column(cursor, table, col_name, col_type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
        print(f"Added column {col_name} to {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column {col_name} already exists in {table}")
        else:
            print(f"Error adding {col_name} to {table}: {e}")

processed = False

for db_file in DB_FILES:
    if os.path.exists(db_file):
        print(f"Processing {db_file}...")
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Phase 3 columns
            add_check_column(cursor, "user", "whatsapp_number", "VARCHAR(20)")
            add_check_column(cursor, "user", "family_whatsapp", "VARCHAR(20)")
            
            # Phase 4 columns - Adding preferred_language
            try:
                cursor.execute("ALTER TABLE user ADD COLUMN preferred_language VARCHAR(10) DEFAULT 'english'")
                print("Added preferred_language to user")
            except sqlite3.OperationalError as e:
                print(f"preferred_language error: {e}")

            conn.commit()
            conn.close()
            print(f"Migration complete for {db_file}.")
            processed = True
        except Exception as e:
            print(f"Failed to process {db_file}: {e}")
            
if not processed:
    print("No database files found to migrate.")
