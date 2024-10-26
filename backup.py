__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/26'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'  # 'Production / Development'
__version__ = '1.0.5'


import os
import shutil
import hashlib
import zipfile
import logging
import asyncio
import aiofiles
from datetime import datetime
from colorlog import ColoredFormatter
from dotenv import load_dotenv


load_dotenv()


class BackupManager:
    def __init__(self):
        self.setup_logging()

        self.server_dir = self.get_env_variable('SERVER_DIR')
        self.server_start_file = self.get_env_variable('SERVER_START_FILE')
        self.server_stop_file = self.get_env_variable('SERVER_STOP_FILE')
        self.databases_dir = self.get_env_variable('DATABASES_DIR')
        self.backup_dir = self.get_env_variable('BACKUP_DIR')

        self.db_extension = os.getenv('DB_EXTENSION', '.DBX')
        self.active_db_extensions = [ext.strip() for ext in os.getenv('ACTIVE_DB_EXTENSIONS', '.PRE').split(',')]
        self.archive_format = os.getenv('ARCHIVE_FORMAT', 'zip')
        self.path_separator = os.getenv('PATH_SEPARATOR', ' ')


    @staticmethod
    def get_env_variable(var_name: str) -> str:
        value = os.getenv(var_name)
        if value is None:
            logging.error(f"ERROR: Environment variable {var_name} is not set")
            raise ValueError(f"ERROR: Environment variable {var_name} is not set")
        logging.info(f"Environment variable {var_name} is set to {value}")
        return value


    @staticmethod
    def setup_logging():
        formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"log_{datetime.now().strftime('%Y-%m-%d')}.log"),
                handler
            ]
        )


    @staticmethod
    async def calculate_hash(file_path):
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            while True:
                chunk = await f.read(4096)
                if not chunk:
                    break
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


    @staticmethod
    async def has_sufficient_space(backup_path: str, db_path: str) -> bool:
        return shutil.disk_usage(backup_path).free > os.path.getsize(db_path)


    @staticmethod
    async def delete_oldest_backup(db_path) -> None:
        logging.info(f"Deleting oldest backup for {db_path}.")


    async def stop_server(self) -> None:
        try:
            shutil.copy(self.server_stop_file, self.server_dir)
            logging.info("Server stop command issued.")
        except Exception as e:
            logging.error(f"Failed to issue server stop command: {e}")


    async def start_server(self) -> None:
        try:
            os.startfile(self.server_start_file)
            logging.info("Server started.")
        except Exception as e:
            logging.error(f"Failed to start server: {e}")


    async def check_active_files(self, db_path: str) -> bool:
        for ext in self.active_db_extensions:
            if os.path.exists(db_path + ext):
                return True
        return False


    async def perform_backup(self) -> None:
        for root, _, files in os.walk(self.databases_dir):
            for file in files:
                if file.endswith(self.db_extension):
                    db_path = os.path.join(root, file)
                    if await self.check_active_files(db_path):
                        logging.info(f"Database {db_path} is active, skipping backup.")
                        continue

                    current_hash = await self.calculate_hash(db_path)
                    hash_file_path = os.path.join(self.backup_dir, f"{file}.hash")

                    if os.path.exists(hash_file_path):
                        async with aiofiles.open(hash_file_path, 'r') as hash_file:
                            last_hash = await hash_file.read()
                            if current_hash == last_hash:
                                logging.info(f"No changes in {db_path}, skipping backup.")
                                continue

                    today = datetime.now().strftime("%Y-%m-%d")
                    backup_path = os.path.join(self.backup_dir, datetime.now().strftime("%Y"),
                                               datetime.now().strftime("%m"), today)
                    os.makedirs(backup_path, exist_ok=True)

                    while not await self.has_sufficient_space(backup_path, db_path):
                        await self.delete_oldest_backup(db_path)

                    archive_name = f"{self.path_separator.join(os.path.relpath(root, self.databases_dir).split(os.sep))}_{today}.{self.archive_format}"
                    archive_path = os.path.join(backup_path, archive_name)

                    try:
                        with zipfile.ZipFile(archive_path, 'w') as archive:
                            archive.write(db_path, file)
                        async with aiofiles.open(hash_file_path, 'w') as hash_file:
                            await hash_file.write(current_hash)
                        logging.info(f"Backup completed for {db_path}.")
                    except Exception as e:
                        logging.error(f"Failed to backup {db_path}: {e}")
                        await self.delete_oldest_backup(db_path)  # Re-attempt after deleting old backups
                        continue


    async def execute(self):
        await self.stop_server()
        await self.perform_backup()
        await self.start_server()


if __name__ == "__main__":
    try:
        backup_manager = BackupManager()
        asyncio.run(backup_manager.execute())
    except KeyboardInterrupt:
        print("Execution was interrupted by the user.")
    except ValueError as err:
        print(err)