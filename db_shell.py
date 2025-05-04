import sqlite3
import os
from pathlib import Path

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent

# Connect to the database
conn = sqlite3.connect(BASE_DIR / "db.sqlite3")
cursor = conn.cursor()

try:
    while True:
        # Get SQL input from user
        sql = input("sqlite> ")
        
        # Check for exit command
        if sql.lower() in ('exit', 'quit', '.quit', '.exit'):
            break
            
        # Execute the query
        try:
            cursor.execute(sql)
            
            # Fetch and display results
            results = cursor.fetchall()
            if results:
                # Get column names
                column_names = [description[0] for description in cursor.description]
                print("\n|", " | ".join(column_names), "|")
                print("-" * (sum(len(name) + 3 for name in column_names) + 1))
                
                # Print each row
                for row in results:
                    print("|", " | ".join(str(value) for value in row), "|")
            
            # Show number of rows affected for non-SELECT queries
            if cursor.rowcount >= 0 and not results:
                print(f"\n{cursor.rowcount} rows affected.")
            
            # Commit after each statement (except SELECT)
            if not sql.lower().strip().startswith('select'):
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error: {e}")
            
except KeyboardInterrupt:
    print("\nExiting...")

finally:
    cursor.close()
    conn.close()
