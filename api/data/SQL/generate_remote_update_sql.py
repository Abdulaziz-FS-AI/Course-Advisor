import pandas as pd
import os

csv_path = "/home/shared_dir/data/SQL/departments.csv"
output_file = "/home/shared_dir/data/SQL/verify_remote_update.sql"

def generate_sql():
    if not os.path.exists(csv_path):
        print("CSV not found.")
        return

    df = pd.read_csv(csv_path)
    
    with open(output_file, "w") as f:
        f.write("-- SQL to update Supabase remotely\n")
        f.write("-- Run this in the Supabase SQL Editor\n\n")
        
        # 1. Add Column
        f.write("ALTER TABLE departments ADD COLUMN IF NOT EXISTS link TEXT;\n\n")
        
        # 2. Updates
        f.write("-- Update Links\n")
        for _, row in df.iterrows():
            if pd.notna(row.get('link')):
                # Escape single quotes if any (though unlikely in URLs)
                link = str(row['link']).replace("'", "''")
                dept_id = row['id']
                # Use ID as stable identifier
                f.write(f"UPDATE departments SET link = '{link}' WHERE id = {dept_id};\n")
                
    print(f"Generated SQL at {output_file}")

if __name__ == "__main__":
    generate_sql()
