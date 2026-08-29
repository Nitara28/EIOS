import sqlite3

DB_PATH = "backend/eios.db"

connection = sqlite3.connect(DB_PATH)

try:
    cursor = connection.cursor()

    columns = {
        row[1]
        for row in cursor.execute("PRAGMA table_info(actions)").fetchall()
    }

    if "execution_mode" not in columns:
        cursor.execute(
            "ALTER TABLE actions "
            "ADD COLUMN execution_mode VARCHAR(20) "
            "NOT NULL DEFAULT 'DEMO'"
        )
        print("Added execution_mode")

    if "external_confirmation" not in columns:
        cursor.execute(
            "ALTER TABLE actions "
            "ADD COLUMN external_confirmation BOOLEAN "
            "NOT NULL DEFAULT 0"
        )
        print("Added external_confirmation")

    connection.commit()
    print("Migration successful")

finally:
    connection.close()