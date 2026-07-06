import sys
import os

# Ensure backend directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Running offline syntax and import checks for the modified components...")

try:
    # 1. Test model import
    from maintenance_module.model import MaintenanceAlert
    print("[OK] Successfully imported MaintenanceAlert model.")
    
    # Check if last_notified_at column is defined in the model
    if hasattr(MaintenanceAlert, 'last_notified_at'):
        print("[OK] Verified last_notified_at column is present in SQLAlchemy model.")
    else:
        print("[ERROR] last_notified_at column is missing in SQLAlchemy model!")
        sys.exit(1)
        
    # 2. Test reminder service import
    from maintenance_module.reminder_service import check_and_send_critical_reminders, start_reminder_scheduler
    print("[OK] Successfully imported check_and_send_critical_reminders and start_reminder_scheduler.")
    
    # 3. Test migrations import
    from database.db import run_migrations
    print("[OK] Successfully imported run_migrations.")
    
    # 4. Test main import
    import main
    print("[OK] Successfully imported main module (Lifespan and App check).")
    
    print("\nALL OFFLINE CHECKS COMPLETED SUCCESSFULLY! No syntax or import errors found.")
    
except Exception as e:
    print(f"\n[ERROR] IMPORT OR SYNTAX ERROR: {e}")
    sys.exit(1)
