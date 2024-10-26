__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/26'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'  # 'Production / Development'
__version__ = '1.0.0'


import os
import shutil
import hashlib
from datetime import datetime
import zipfile
import logging
from dotenv import load_dotenv


load_dotenv()

# Constants from env
SERVER_DIR = os.getenv('SERVER_DIR', r'F:\Softland Systems\SLS-Serv')
SERVER_START_FILE = os.getenv('SERVER_START_FILE', r'F:\Softland Systems\SLS-Serv\monitor.exe')
SERVER_STOP_FILE = os.getenv('SERVER_STOP_FILE', r'F:\Softland Systems\SLS-Serv\Exit\Z_Cmnd.tmp')
DATABASES_DIR = os.getenv('DATABASES_DIR', r'F:\Softland Systems\DB\DBX')
BACKUP_DIR = os.getenv('BACKUP_DIR', r'H:\SLS-backup')
DB_EXTENSION = os.getenv('DB_EXTENSION', '.DBX')
ACTIVE_DB_EXTENSIONS = [ext.strip() for ext in os.getenv('ACTIVE_DB_EXTENSIONS', '.PRE, .SHN, .SHR, .TTS').split(',')]
ARCHIVE_FORMAT = os.getenv('ARCHIVE_FORMAT', 'zip')
PATH_SEPARATOR = os.getenv('PATH_SEPARATOR', ' ')


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"log_{datetime.now().strftime('%Y-%m-%d')}.log"),
        logging.StreamHandler()
    ])


def stop_server():
    # Copy stop server file to server directory
    try:
        shutil.copy(SERVER_STOP_FILE, SERVER_DIR)
        logging.info("Server stop command issued.")
    except Exception as e:
        logging.error(f"Failed to issue server stop command: {e}")


def start_server():
    # Start server process
    try:
        os.startfile(SERVER_START_FILE)
        logging.info("Server started.")
    except Exception as e:
        logging.error(f"Failed to start server: {e}")


def calculate_hash(file_path):
    # Calculate SHA256 hash of a file
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def check_active_files(db_path):
    # Check for active DB files
    for ext in ACTIVE_DB_EXTENSIONS:
        if os.path.exists(db_path + ext):
            return True
    return False


def perform_backup():
    for root, _, files in os.walk(DATABASES_DIR):
        for file in files:
            if file.endswith(DB_EXTENSION):
                db_path = os.path.join(root, file)
                if check_active_files(db_path):
                    logging.info(f"Database {db_path} is active, skipping backup.")
                    continue

                # Calculate current DB hash
                current_hash = calculate_hash(db_path)
                hash_file_path = os.path.join(BACKUP_DIR, f"{file}.hash")

                # Check existing backup hash
                if os.path.exists(hash_file_path):
                    with open(hash_file_path, 'r') as hash_file:
                        last_hash = hash_file.read()
                        if current_hash == last_hash:
                            logging.info(f"No changes in {db_path}, skipping backup.")
                            continue

                # Create backup directory structure
                today = datetime.now().strftime("%Y-%m-%d")
                backup_path = os.path.join(BACKUP_DIR, datetime.now().strftime("%Y"), datetime.now().strftime("%m"),
                                           today)
                os.makedirs(backup_path, exist_ok=True)

                # Ensure enough space and delete oldest backup if necessary
                while not has_sufficient_space(backup_path, db_path):
                    delete_oldest_backup(db_path)

                # Archive database
                archive_name = f"{PATH_SEPARATOR.join(os.path.relpath(root, DATABASES_DIR).split(os.sep))}_{today}.{ARCHIVE_FORMAT}"
                archive_path = os.path.join(backup_path, archive_name)

                try:
                    with zipfile.ZipFile(archive_path, 'w') as archive:
                        archive.write(db_path, file)
                    # Update hash file
                    with open(hash_file_path, 'w') as hash_file:
                        hash_file.write(current_hash)
                    logging.info(f"Backup completed for {db_path}.")
                except Exception as e:
                    logging.error(f"Failed to backup {db_path}: {e}")
                    delete_oldest_backup(db_path)  # Re-attempt after deleting old backups
                    continue


def has_sufficient_space(backup_path, db_path):
    # Check free space logic here
    return shutil.disk_usage(backup_path).free > os.path.getsize(db_path)


def delete_oldest_backup(db_path):
    # Logic to find and delete oldest backup
    logging.info(f"Deleting oldest backup for {db_path}.")
    # Code to determine and delete oldest backup here


def main():
    stop_server()
    perform_backup()
    start_server()


if __name__ == "__main__":
    main()
