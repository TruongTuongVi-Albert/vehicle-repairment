import mysql.connector
from config import Config

def update_schema():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            ssl_disabled=Config.MYSQL_SSL_DISABLED
        )
        cursor = conn.cursor()
        
        print("Connected to database...")
        
        # 2. Update repair_details table
        print("Updating reception_slips table...")
        try:
            # Make component_id nullable in repair_details
            cursor.execute("ALTER TABLE repair_details MODIFY COLUMN component_id INT NULL")
            print("Modified component_id to be nullable in repair_details.")
        except mysql.connector.Error as err:
            print(f"Skipping repair_details update: {err}")

        # 3. Add is_deleted to components table
        print("Updating components table...")
        try:
            cursor.execute("ALTER TABLE components ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE")
            print("Added is_deleted column to components.")
        except mysql.connector.Error as err:
            print(f"Skipping components update: {err}")

        conn.commit()
        cursor.close()
        conn.close()
        print("Schema update completed.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_schema()
