import os
import subprocess
from datetime import datetime

def backup_database():
    """Backup the database to a SQL file."""
    backup_dir = "./backups"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"backup_{timestamp}.sql")

    try:
        # Replace 'your_username' and 'your_password' with actual database credentials
        command = f"mysqldump -u your_username -pyour_password prj_insurance > {backup_file}"
        subprocess.run(command, shell=True, check=True)
        print(f"Backup successful! File saved at: {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e}")

def restore_database(backup_file):
    """Restore the database from a SQL file."""
    try:
        # Replace 'your_username' and 'your_password' with actual database credentials
        command = f"mysql -u your_username -pyour_password prj_insurance < {backup_file}"
        subprocess.run(command, shell=True, check=True)
        print("Database restored successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Restore failed: {e}")

if __name__ == "__main__":
    print("1. Backup Database")
    print("2. Restore Database")
    choice = input("Enter your choice: ")

    if choice == "1":
        backup_database()
    elif choice == "2":
        backup_file = input("Enter the path to the backup file: ")
        restore_database(backup_file)
    else:
        print("Invalid choice!")
