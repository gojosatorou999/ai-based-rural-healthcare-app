import sqlite3
import csv
import os

def export_symptom_reports_to_csv():
    # Detect database path
    db_path = 'c:/Users/risha/Documents/antigrav/instance/database.db'
    if not os.path.exists(db_path):
        db_path = 'c:/Users/risha/Documents/antigrav/database.db'

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    # Detect export path
    export_path = 'c:/Users/risha/Documents/antigrav/symptom_reports_export.csv'

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Join with User table to get patient names
        query = """
        SELECT 
            sr.id, sr.user_id, u.username, sr.symptoms_text, sr.affected_area, 
            sr.severity, sr.duration, sr.ai_prediction, sr.confidence_score, 
            sr.doctor_approved, sr.doctor_notes, sr.created_at
        FROM symptom_report sr
        JOIN user u ON sr.user_id = u.id
        ORDER BY sr.created_at DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]

        with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(column_names)
            writer.writerows(rows)

        print(f"Successfully exported {len(rows)} reports to {export_path}")
        return export_path

    except Exception as e:
        print(f"Error during export: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    export_symptom_reports_to_csv()
