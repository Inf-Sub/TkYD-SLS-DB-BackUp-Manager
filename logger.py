__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2025/04/13'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'  # 'Production / Development'
__version__ = '1.0.2.5'


import logging
import logging.config
from colorlog import ColoredFormatter
from pathlib import Path
from typing import List, Optional
# from datetime import datetime

from config import Config


def setup_logger(log_file: Optional[str] = None) -> str:
    """
    Configures the logging settings, including file paths and formats.

    :param log_file: The file path for logging; if not provided, it defaults to the environment setting.

    :return: None
    """
    env: dict = Config().get_config('log')

    log_level_console: str = env.get('log_level_console')
    log_level_file: str = env.get('log_level_file')
    log_format_console: str = env.get('log_format_console')
    log_format_file: str = env.get('log_format_file')
    log_console_language: str = env.get('log_console_language')

    if log_file is None:
        log_file = env.get('log_path')

    log_path = Path(log_file).parent
    log_path.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': log_format_file,
            },
            'colored': {
                '()': ColoredFormatter,
                'format': log_format_console,
                'datefmt': None,
                'reset': True,
                'log_colors': {
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red',
                }
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'colored',
                'level': log_level_console,
            },
            'rotating_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'standard',
                'level': log_level_file,
                'filename': log_file,
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 5,
            },
        },
        'root': {'handlers': ['console', 'rotating_file'], 'level': 'INFO', },
    })

    log_ignore_list: List[str] = [
        # 'smbprotocol'
    ]

    for logger_name in log_ignore_list:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
        
    return log_console_language


def change_log_levels(console_level: str, file_level: str) -> None:
    """
    Change the logging levels for console and file handlers.

    :param console_level: The logging level for console output.
    :param file_level: The logging level for file output.

    :return: None
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(console_level)
        elif isinstance(handler, logging.handlers.RotatingFileHandler):
            handler.setLevel(file_level)


if __name__ == '__main__':
    setup_logger()

    # Example on how to change log levels dynamically
    # This should be replaced with the actual logic for reading the new levels
    new_console_level = 'INFO'
    new_file_level = 'ERROR'
    change_log_levels(new_console_level, new_file_level)
    
    # test
    logger = logging.getLogger(__name__)
    logger.info('Hello World!')


# def setup_logging():
#     """
#     Настраивает логирование для приложения.
#
#     Этот метод конфигурирует форматирование логов и устанавливает обработчики для вывода логов\n
#     как в консоль, так и в файл.
#     """
#     formatter = ColoredFormatter(
#         '%(filename)s:%(lineno)d\n%(log_color)s%(asctime)-24s| %(levelname)-8s| %(name)-8s\t| %(funcName)-16s| %('
#         'message)s',
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
#         format='%(asctime)-24s| %(levelname)-8s| %(name)-8s\t| %(funcName)-16s| %(message)s',
#         handlers=[
#             logging.FileHandler(f"log_{datetime.now().strftime('%Y-%m-%d')}.log"),
#             handler
#         ]
#     )
#
#
# if __name__ == "__main__":
#     setup_logging()