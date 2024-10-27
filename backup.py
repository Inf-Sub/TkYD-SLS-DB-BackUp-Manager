__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/27'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '1.1.7.4'


import os
import shutil
import hashlib
import zipfile
# import logging
# from colorlog import ColoredFormatter
import asyncio
import aiofiles
import aiosqlite
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Awaitable
# import tracemalloc

from logger import configure_logging


# Загрузка логгера с настройками
logging = configure_logging()


class BackupManager:
    def __init__(self):
        """
        Инициализатор класса BackupManager.
        Настраивает логирование и инициализирует переменные окружения,
        которые используются для конфигурации путей и форматов резервного копирования.
        """
        load_dotenv()

        # Инициализация переменных окружения для различных директорий и файлов
        self.server_dir = self.get_env_variable('SERVER_DIR')
        self.server_start_file = self.get_env_variable('SERVER_START_FILE')
        self.server_stop_file = self.get_env_variable('SERVER_STOP_FILE')
        self.databases_dir = self.get_env_variable('DATABASES_DIR')
        self.backup_dir = self.get_env_variable('BACKUP_DIR')

        # Настройки по умолчанию для расширений файлов и форматов архивов
        self.sqlite_db_file = os.getenv('SQLITE_DB_PATH', 'backup_metadata.db')
        self.ignored_keywords = [kw.strip() for kw in os.getenv('IGNORED_KEYWORDS', '').split(',')]
        self.archive_name_format = os.getenv('ARCHIVE_NAME_FORMAT', '{db_path}_{db_name}_{date_time}')
        self.db_extension = os.getenv('DB_EXTENSION', '.DBX')
        self.active_db_extensions = [ext.strip() for ext in os.getenv('ACTIVE_DB_EXTENSIONS', '.PRE').split(',')]
        self.archive_format = os.getenv('ARCHIVE_FORMAT', '.zip')
        self.path_separator = os.getenv('PATH_SEPARATOR', ' ')
        # self.log_folder = os.getenv('LOG_FOLDER', 'logs')
        # self.log_file_template = os.getenv('LOG_FILE_TEMPLATE', 'log_%Y-%m-%d.log')
        # self.log_format = os.getenv('LOG_FORMAT', '%(asctime)s - %(levelname)6s - %(message)s')

        self.sqlite_db_path = os.path.join(self.databases_dir, self.sqlite_db_file)


    # async def initialize(self):
    #     await self.setup_logging()
    #
    #
    # async def setup_logging(self) -> None:
    #     """
    #     Настраивает систему логирования для записи логов в файл и отображения их в консоли с цветным форматированием.
    #     """
    #     formatter = ColoredFormatter(
    #         f'%(log_color)s{self.log_format}',
    #         datefmt=None,
    #         reset=True,
    #         log_colors={
    #             'DEBUG': 'cyan',
    #             'INFO': 'green',
    #             'WARNING': 'yellow',
    #             'ERROR': 'red',
    #             'CRITICAL': 'red,bg_white',
    #         }
    #     )
    #     handler = logging.StreamHandler()
    #     handler.setFormatter(formatter)
    #     logging.basicConfig(
    #         level=logging.INFO,
    #         format=self.log_format,
    #         handlers=[
    #             await self._get_file_handler(),
    #             handler
    #         ]
    #     )
    #
    #
    # # async def _get_file_handler(self) -> Awaitable[logging.FileHandler]:
    # async def _get_file_handler(self):
    #     """
    #     Асинхронный метод для получения обработчика файла логирования.
    #
    #     Returns:
    #         Awaitable[logging.FileHandler]: Объект обработчика файла логирования.
    #     """
    #     # Объединяем путь к папке и шаблон файла
    #     full_path_template = os.path.join(self.log_folder, self.log_file_template)
    #     # Формируем полный путь к файлу на основе текущей даты и времени
    #     filename = datetime.now().strftime(full_path_template)
    #     # Создаем необходимые каталоги, если их нет
    #     os.makedirs(os.path.dirname(filename), exist_ok=True)
    #     # Открываем файл асинхронно в режиме добавления, чтобы проверить возможность записи
    #     async with aiofiles.open(filename, 'a'):
    #         # Возвращаем экземпляр обработчика файла логирования
    #         return logging.FileHandler(filename)


    @staticmethod
    def get_env_variable(var_name: str) -> str:
        """
        Получает значение переменной окружения и логирует её.

        :param var_name: Имя переменной окружения.
        :return: Значение переменной окружения.
        :raises ValueError: Если переменная окружения не установлена.
        """
        value = os.getenv(var_name)
        if value is None:
            logging.error(f'Environment variable {var_name} is not set')
            raise ValueError(f'Environment variable {var_name} is not set')
        logging.info(f'Environment variable {var_name} is set to {value}')
        return value


    @staticmethod
    async def calculate_hash(file_path: str) -> str:
        """
        Асинхронно вычисляет SHA-256 хеш для указанного файла.

        :param file_path: Путь к файлу.
        :return: Хеш файла в виде шестнадцатеречной строки.
        """
        logging.debug(f'Starting hash calculation for {file_path}.')
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                chunk = await f.read(4096)
                if not chunk:
                    break
                hash_sha256.update(chunk)
        hash_hex = hash_sha256.hexdigest()
        logging.info(f'Hash calculation completed for {file_path}. Hash: {hash_hex}')
        return hash_hex


    @staticmethod
    async def has_sufficient_space(backup_path: str, db_path: str) -> bool:
        """
        Проверяет, достаточно ли свободного места в указанной директории для резервного копирования.

        :param backup_path: Путь к директории резервного копирования.
        :param db_path: Путь к базе данных.
        :return: True, если достаточно места, иначе False.
        """
        logging.debug(f'Checking sufficient space in {backup_path} for database {db_path}.')
        free_space = shutil.disk_usage(backup_path).free
        db_size = os.path.getsize(db_path)
        if free_space > db_size:
            logging.info(f'Sufficient space available in {backup_path}.')
            return True
        else:
            logging.warning(f'Insufficient space in {backup_path} for the database {db_path}.')
            return False


    @staticmethod
    async def delete_oldest_backup(db_path) -> None:
        """
        Удаляет самый старый бэкап для заданной базы данных.

        :param db_path: Путь к базе данных.
        """
        logging.warning(f'Deleting oldest backup for {db_path}.')
        # Placeholder for the delete operation


    @staticmethod
    async def remove_prefix(text: str, prefix: str) -> str:
        return text[len(prefix):] if text.startswith(prefix) else text



    async def setup_database(self) -> None:
        async with aiosqlite.connect(self.sqlite_db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY,
                    db_path TEXT NOT NULL,
                    backup_path TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL
                )
            ''')
            await db.commit()


    async def save_backup_metadata(self, db_path: str, backup_path: str, hash_value: str) -> None:
        async with aiosqlite.connect(self.sqlite_db_path) as db:
            await db.execute('''
                INSERT INTO backups (db_path, backup_path, hash)
                VALUES (?, ?, ?)
            ''', (db_path, backup_path, hash_value))
            await db.commit()


    async def get_last_hash(self, db_path: str) -> Optional[str]:
        async with aiosqlite.connect(self.sqlite_db_path) as db:
            async with db.execute(
                    'SELECT hash FROM backups WHERE db_path = ? ORDER BY timestamp DESC LIMIT 1', (db_path,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None


    async def stop_server(self) -> None:
        """
        Останавливает сервер, копируя файл остановки в нужную директорию.
        """
        if os.path.exists(self.server_stop_file):
            try:
                shutil.copy(self.server_stop_file, self.server_dir)
                logging.warning('Server stop command issued.')
            except Exception as e:
                logging.error(f'Failed to issue server stop command: {e}')
        else:
            logging.error('Server stop file does not exist.')
            # Заглушаем ошибку и завершаем выполнение программы
            raise FileNotFoundError('We are finishing the program execution.')


    async def start_server(self) -> None:
        """
        Запускает сервер, используя системный вызов для открытия файла запуска.
        """
        try:
            os.startfile(self.server_start_file)
            logging.warning('Server started.')
        except Exception as e:
            logging.error(f'Failed to start server: {e}')


    async def check_active_files(self, db_path: str) -> bool:
        """
        Проверяет наличие активных файлов с заданным путем к базе данных.

        :param db_path: Путь к файлу базы данных.
        :return: True, если есть активные файлы, иначе False.
        """
        for ext in self.active_db_extensions:
            if os.path.exists(f'{db_path}{ext}'):
                return True
        return False


    async def perform_backup(self) -> None:
        """
        Выполняет резервное копирование всех баз данных в заданной директории.
        Проверяет наличие изменений в файлах и создает архивы только для тех баз, которые были изменены.
        Также следит за свободным пространством и удаляет старые резервные копии, если это необходимо.
        """
        await self.setup_database()

        # Проходим по всем файлам в директории с базами данных
        for root, _, files in os.walk(self.databases_dir):
            # Игнорируем папку с бэкапами, если она находится в папке с базами данных
            if os.path.commonpath([root, self.backup_dir]) == self.backup_dir:
                logging.info(f'Skipping backup directory: {root}')
                continue

            for file in files:
                # Проверяем, имеет ли файл нужное расширение для базы данных
                if file.endswith(self.db_extension):
                    logging.info(f'File: {file} -  file.endswith: {file.endswith(self.db_extension)}.')
                    db_path = os.path.join(root, file)

                    # Игнорируем файлы, содержащие любое из ключевых слов в имени
                    if any(keyword in file for keyword in self.ignored_keywords):
                        logging.warning(f'Ignoring file with ignored keywords in name: {file}')
                        continue

                    # Проверяем, активен ли файл базы данных (например, открыт другой программой)
                    if await self.check_active_files(db_path):
                        logging.info(f'Database {db_path} is active, skipping backup.')
                        continue

                    # # Вычисляем хэш текущего состояния файла для определения изменений
                    # current_hash = await self.calculate_hash(db_path)
                    # hash_file_path = os.path.join(self.backup_dir, f'{file}.hash')
                    #
                    # # Если хэш файла уже существует, читаем его и сравниваем с текущим
                    # if os.path.exists(hash_file_path):
                    #     async with aiofiles.open(hash_file_path, 'r') as hash_file:
                    #         last_hash = await hash_file.read()
                    #         if current_hash == last_hash:
                    #             logging.info(f'No changes in {db_path}, skipping backup.')
                    #             continue

                    # Вычисляем хэш текущего состояния файла для определения изменений
                    current_hash = await self.calculate_hash(db_path)
                    last_hash = await self.get_last_hash(db_path)

                    if current_hash == last_hash:
                        logging.info(f'No changes in {db_path}, skipping backup.')
                        continue

                    # Определяем путь для сохранения резервной копии на основе текущей даты
                    today = datetime.now().strftime('%Y-%m-%d')
                    backup_path = os.path.join(self.backup_dir, datetime.now().strftime('%Y'),
                                               datetime.now().strftime('%m'), today)
                    os.makedirs(backup_path, exist_ok=True)

                    # Проверяем, достаточно ли свободного пространства для резервного копирования
                    while not await self.has_sufficient_space(backup_path, db_path):
                        # Если места недостаточно, удаляем старейшие резервные копии
                        await self.delete_oldest_backup(db_path)

                    # Создаем имя архива, включая относительный путь базы данных и текущую дату
                    rel_db_path = os.path.relpath(root, self.databases_dir).replace(os.sep, self.path_separator)

                    archive_name = f'{self.archive_name_format.format(
                        db_path=rel_db_path, db_name=file, date_time=today)}{self.archive_format}'
                    # Если файл находится в корневой директории DATABASES_DIR
                    prefix = f'.{self.path_separator}'
                    if rel_db_path == prefix:
                        archive_name = await self.remove_prefix(archive_name, prefix)

                    archive_path = os.path.join(backup_path, archive_name)

                    try:
                        # Создаем архив с текущей базой данных
                        with zipfile.ZipFile(archive_path, 'w') as archive:
                            archive.write(db_path, file)

                        # Сохраняем новый хэш файла, чтобы отслеживать изменения в будущем
                        # async with aiofiles.open(hash_file_path, 'w') as hash_file:
                        #     await hash_file.write(current_hash)
                        # Save metadata to database
                        await self.save_backup_metadata(db_path, archive_path, current_hash)

                        logging.info(f'Backup completed for {db_path}.')
                    except Exception as e:
                        # Логируем ошибку, если резервное копирование не удалось, и пытаемся удалить старые копии
                        logging.error(f'Failed to backup {db_path}: {e}')
                        await self.delete_oldest_backup(
                            db_path)  # Повторная попытка после удаления старых резервных копий
                        continue


    async def execute(self) -> None:
        """
        Запускает процесс резервного копирования, останавливая сервер перед процессом и перезапуская его после завершения.
        """
        try:
            # await self.initialize()
            await self.stop_server()
            await self.perform_backup()
            await self.start_server()
        except FileNotFoundError as e:
            logging.error(e)


if __name__ == "__main__":
    # tracemalloc.start()

    try:
        backup_manager = BackupManager()
        asyncio.run(backup_manager.execute())
    except KeyboardInterrupt:
        logging.info('Execution was interrupted by the user.')  # print
    except ValueError as ve:
        print(str(ve))

    # tracemalloc.stop()
