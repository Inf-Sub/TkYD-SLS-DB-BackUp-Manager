Для оптимизации и улучшения структуры кода предлагаю использовать объектно-ориентированный подход. Мы создадим класс для управления сервером и выполнения резервного копирования. Также добавим цветное логирование для консоли, используя модуль colorlog. Асинхронность можно внедрить с помощью библиотеки asyncio и асинхронных функций.

Вот обновленный код:
`
import os
import shutil
import hashlib
from datetime import datetime
import zipfile
import logging
import colorlog
import asyncio
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class ServerBackupManager:
    def __init__(self):
        # Инициализация настроек из переменных окружения
        self.server_dir = os.getenv('SERVER_DIR', r'F:\Softland Systems\SLS-Serv')
        self.server_start_file = os.getenv('SERVER_START_FILE', r'F:\Softland Systems\SLS-Serv\monitor.exe')
        self.server_stop_file = os.getenv('SERVER_STOP_FILE', r'F:\Softland Systems\SLS-Serv\Exit\Z_Cmnd.tmp')
        self.databases_dir = os.getenv('DATABASES_DIR', r'F:\Softland Systems\DB\DBX')
        self.backup_dir = os.getenv('BACKUP_DIR', r'H:\SLS-backup')
        self.db_extension = os.getenv('DB_EXTENSION', '.DBX')
        self.active_db_extensions = [ext.strip() for ext in os.getenv('ACTIVE_DB_EXTENSIONS', '.PRE, .SHN, .SHR, .TTS').split(',')]
        self.archive_format = os.getenv('ARCHIVE_FORMAT', 'zip')
        self.path_separator = os.getenv('PATH_SEPARATOR', ' ')

        # Настройка логирования с цветом
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        ))

        self.logger = logging.getLogger('ServerBackupManager')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    async def stop_server(self):
        try:
            shutil.copy(self.server_stop_file, self.server_dir)
            self.logger.info("Server stop command issued.")
        except Exception as e:
            self.logger.error(f"Failed to issue server stop command: {e}")

    async def start_server(self):
        try:
            os.startfile(self.server_start_file)
            self.logger.info("Server started.")
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")

    async def calculate_hash(self, file_path):
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    async def check_active_files(self, db_path):
        for ext in self.active_db_extensions:
            if os.path.exists(db_path + ext):
                return True
        return False

    async def perform_backup(self):
        for root, _, files in os.walk(self.databases_dir):
            for file in files:
                if file.endswith(self.db_extension):
                    db_path = os.path.join(root, file)
                    if await self.check_active_files(db_path):
                        self.logger.info(f"Database {db_path} is active, skipping backup.")
                        continue

                    # Calculate current DB hash
                    current_hash = await self.calculate_hash(db_path)
                    hash_file_path = os.path.join(self.backup_dir, f"{file}.hash")

                    # Check existing backup hash
                    if os.path.exists(hash_file_path):
                        with open(hash_file_path, 'r') as hash_file:
                            last_hash = hash_file.read()
                            if current_hash == last_hash:

`
