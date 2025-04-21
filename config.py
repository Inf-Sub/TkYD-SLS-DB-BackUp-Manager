__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2025/04/13'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'  # 'Production / Development'
__version__ = '1.0.3.0'


from os import getenv
from os.path import join as os_join
# from decouple import config
from dotenv import load_dotenv
from datetime import datetime as dt
import logging


class Config:
    def __init__(self):
        # Загрузка переменных окружения из файла .env
        load_dotenv()
        self.env = self.load_env()

    @staticmethod
    def load_env() -> dict:
        """
        Загрузка переменных окружения из файла .env.
        
        :return: Возвращает словарь с параметрами из .env файла.
        """
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

                'LOG_PATH': getenv('LOG_PATH', 'logs'),
                'LOG_FILE': getenv('LOG_FILE'),
                'LOG_LEVEL_CONSOLE': getenv('LOG_LEVEL_CONSOLE', 'WARNING').upper(),
                'LOG_LEVEL_FILE': getenv('LOG_LEVEL_FILE', 'WARNING').upper(),
                'LOG_FORMAT_CONSOLE': getenv('LOG_FORMAT_CONSOLE').replace(r'\t', '\t').replace(r'\n', '\n'),
                'LOG_FORMAT_FILE': getenv('LOG_FORMAT_FILE').replace(r'\t', '\t').replace(r'\n', '\n'),
                'LOG_CONSOLE_LANGUAGE': getenv('LOG_CONSOLE_LANGUAGE', 'en').lower(),
            }
        except (TypeError, ValueError) as e:
            logging.error(e)
            exit()
    
    def get_config(self, config_type: str) -> dict:
        """
        Получение конфигурации по указанному типу.

        :param config_type: Префикс для поиска переменных окружения.
        :return: Возвращает словарь с параметрами, соответствующими указанному префиксу.
        """
        return {key.lower(): self.env[key] for key in self.env.keys() if f'{key.startswith(config_type.upper())}_'}


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
