__author__ = 'InfSub'
__contact__ = 'https:/t.me/InfSub'
__copyright__ = 'Copyright (C) 2025, [LegioNTeaM] InfSub'
__date__ = '2025/05/10'
__deprecated__ = False
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '1.0.4.7'

from os import getenv
from typing import Dict, Any

# from os.path import join as os_join
# from decouple import __config
from dotenv import load_dotenv
from datetime import datetime as dt
import logging


class Config:
    """Синглтон для загрузки и хранения конфигурации приложения."""
    _instance = None
    
    def __new__(cls, *args, **kwargs) -> 'Config':
        """Создает новый экземпляр класса Config, если он еще не создан.

        :param args: Позиционные аргументы.
        :param kwargs: Именованные аргументы.
        :return: Экземпляр класса Config.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация экземпляра Config.

        Загружает переменные окружения из файла .env и инициализирует параметры.
        """
        # Проверяем, инициализирован ли уже экземпляр
        if not hasattr(self, '_initialized'):
            self._initialized = True  # Устанавливаем флаг инициализации
            logging.info('Загрузка переменных окружения из файла .env')
            load_dotenv()
            self._current_date = dt.now()
            self._env = self._load_env()
    
    def _load_env(self) -> Dict[str, Any]:
        """
        Загрузка переменных окружения из файла .env.

        :return: Возвращает словарь с параметрами из файла .env.
        """
        current_date = self._current_date
        try:
            return {
                'SERVER_DIR': getenv('SERVER_DIR', r'C:\Softland Systems\SLS-Serv'),
                'SERVER_START_FILE': getenv('SERVER_START_FILE', r'C:\Softland Systems\SLS-Serv\monitor.exe'),
                'SERVER_STOP_FILE': getenv('SERVER_STOP_FILE', r'C:\Softland Systems\SLS-Serv\Exit\Z_Cmnd.tmp'),
                'SERVER_PROCESS_NAME': getenv('SERVER_PROCESS_NAME', 'SLS_Serv.exe'),
                'SERVER_WAIT_SECONDS':
                    int(getenv('SERVER_WAIT_SECONDS')) if getenv('SERVER_WAIT_SECONDS', '').isdigit() else 10,

                'FILES_DIR': getenv('FILES_DIR', r'C:\Softland Systems\DB\DBX'),
                'FILES_BACKUP_DIR': getenv('FILES_BACKUP_DIR', r'C:\Softland Systems\DB\DBX\Backup'),
                'FILES_EXTENSIONS':  [ext.strip() for ext in getenv('FILES_EXTENSIONS', '.DBX').split(',')],
                'FILES_IN_USE_EXTENSIONS': [ext.strip() for ext in getenv('FILES_IN_USE_EXTENSIONS', '.PRE').split(',')],
                'FILES_IGNORE_BACKUP_FILES': getenv('FILES_IGNORE_BACKUP_FILES', 'False').lower() in ('true', '1'),
                'FILES_MIN_REQUIRED_SPACE_GB': (
                    float(getenv('FILES_MIN_REQUIRED_SPACE_GB', '10'))
                    if getenv('FILES_MIN_REQUIRED_SPACE_GB', '').replace('.', '', 1).isdigit() else 10.0
                ),
                'FILES_ARCHIVE_FORMAT': getenv('FILES_ARCHIVE_FORMAT', 'zip'),
                'FILES_7Z_PATH': getenv('FILES_7Z_PATH', r'c:\Program Files\7-Zip\7z'),
                # 'FILES_PATH_SEPARATOR': getenv('FILES_PATH_SEPARATOR', ' '),
                
                'MSG_LANGUAGE': getenv('MSG_LANGUAGE', 'en').lower(),

                'LOG_DIR': current_date.strftime(getenv('LOG_DIR', r'logs\%Y\%Y.%m')),
                'LOG_FILE': current_date.strftime(getenv('LOG_FILE', 'backup_log_%Y.%m.%d.log')),
                'LOG_LEVEL_ROOT': getenv('LOG_LEVEL_ROOT', 'INFO').upper(),
                'LOG_LEVEL_CONSOLE': getenv('LOG_LEVEL_CONSOLE', 'INFO').upper(),
                'LOG_LEVEL_FILE': getenv('LOG_LEVEL_FILE', 'WARNING').upper(),
                'LOG_IGNORE_LIST': getenv('LOG_IGNORE_LIST', ''),
                'LOG_FORMAT_CONSOLE': getenv('LOG_FORMAT_CONSOLE').replace(r'\t', '\t').replace(r'\n', '\n'),
                'LOG_FORMAT_FILE': getenv('LOG_FORMAT_FILE').replace(r'\t', '\t').replace(r'\n', '\n'),
                'LOG_DATE_FORMAT': getenv('LOG_DATE_FORMAT', '%Y.%m.%d %H:%M:%S'),  # Default: None
            }
        except (TypeError, ValueError) as e:
            logging.error(e)
            exit()
    
    def get_config(self, *config_types: str) -> Dict[str, Any]:
        """
        Получение конфигурации по указанным типам.

        :param config_types: Префиксы для поиска переменных окружения.
        :return: Возвращает словарь с параметрами, соответствующими указанным префиксам.
        """
        result = {}
        for config_type in config_types:
            result.update(
                {key.lower(): self._env[key] for key in self._env.keys() if key.startswith(config_type.upper() + '_')})
        return result


if __name__ == "__main__":
    from pprint import pprint
    
    config = Config()
    server_config = config.get_config('SERVER')
    backup_files_config = config.get_config('FILES')
    log_config = config.get_config('LOG')

    print("Server Config:")
    pprint(server_config)
    print()
    print("Backup Files Config:")
    pprint(backup_files_config)
    print()
    print("Log Config:")
    pprint(log_config)
