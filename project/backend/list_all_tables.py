import os
import sys
import subprocess
from sqlalchemy import text

sys.path.append(os.path.dirname(__file__))
from database.db import SessionLocal

def get_all_tables():
    db = SessionLocal()
    try:
        res = db.execute(text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_TYPE = 'BASE TABLE';
        """)).fetchall()
        return [r[0] for r in res]
    except Exception as e:
        print("Failed to get tables:", e)
        return []
    finally:
        db.close()

def main():
    tables = get_all_tables()
    print(f"Found {len(tables)} tables in database.")
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # We will search files for table names
    unused_tables = []
    used_tables = []
    
    for table in tables:
        # Ignore system diagram table
        if table == "sysdiagrams":
            continue
            
        # Count occurrences of table name in Python files in backend
        count = 0
        for root, dirs, files in os.walk(backend_dir):
            # Skip virtualenv and cache dirs
            if "venv" in root or "__pycache__" in root or ".git" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            # search for table name in quotes or table definitions
                            if f'"{table}"' in content or f"'{table}'" in content or f' {table} ' in content:
                                count += 1
                    except Exception:
                        pass
        
        if count == 0:
            unused_tables.append(table)
        else:
            used_tables.append((table, count))
            
    print("\nUsed Tables (and count of referencing Python files):")
    for t, c in sorted(used_tables, key=lambda x: x[1], reverse=True):
        print(f"  - {t}: referenced in {c} files")
        
    print("\nUnused Tables (0 references in backend code):")
    for t in sorted(unused_tables):
        print(f"  - {t}")

if __name__ == "__main__":
    main()
