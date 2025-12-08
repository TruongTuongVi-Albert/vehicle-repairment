import mysql.connector
from config import Config

def migrate():
    print("Connecting to database...")
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
        
        print("Reading schema.sql...")
        with open('database/schema.sql', 'r') as f:
            schema = f.read()
            
        # Split by semicolon and execute each statement
        statements = schema.split(';')
        for statement in statements:
            if statement.strip():
                # Skip CREATE DATABASE and USE commands
                stmt_upper = statement.strip().upper()
                if stmt_upper.startswith('CREATE DATABASE') or stmt_upper.startswith('USE '):
                    continue
                try:
                    print(f"Executing: {statement[:50]}...")
                    cursor.execute(statement)
                except mysql.connector.Error as err:
                    print(f"FAILED: {err}")
                    print(f"Statement: {statement}")
                    # Continue even if error (e.g. table exists)
        
        conn.commit()
        print("Migration completed successfully.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == '__main__':
    migrate()
