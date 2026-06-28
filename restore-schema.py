# python/restore_schema.py
from python.scripts.api_session import engine
# Note the 'scripts' addition here
from python.scripts.api_model_backup import Base 

def restore_db():
    print("Connecting to database to restore core tables...")
    try:
        # This will create the 18 physical tables defined in the backup
        Base.metadata.create_all(bind=engine)
        print("SUCCESS: Core tables restored from python/scripts/api_model_backup.py")
    except Exception as e:
        print(f"FAILED: Schema restoration encountered an error: {e}")

if __name__ == "__main__":
    restore_db()