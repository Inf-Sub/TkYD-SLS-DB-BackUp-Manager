__author__ = 'InfSub'
__contact__ = 'https:/t.me/InfSub'
__copyright__ = 'Copyright (C) 2025, [LegioNTeaM] InfSub'
__date__ = '2025/05/09'
__deprecated__ = False
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '1.0.4.12'

import logging
from logging import config as logging_config
from colorlog import ColoredFormatter
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime as dt

from config import Config


def setup_logger(log_path: Optional[str] = None) -> Optional[str]:
    """
    Configures the logging settings, including file paths and formats.

    :param log_path: The file path for logging; if not provided, it defaults to the environment setting.

    :return: None
    """
    config: Dict[str, Any] = Config().get_config('log')
    
    log_level_console: str = config.get('log_level_console')
    log_level_file: str = config.get('log_level_file')
    log_level_root: str = config.get('log_level_root', 'INFO')
    log_format_console: str = config.get('log_format_console')
    log_format_file: str = config.get('log_format_file')
    # Преобразуем строку в список, удаляя пустые значения
    log_ignore_list: List[str] = [item.strip() for item in config.get('log_ignore_list', '').split(',') if item.strip()]
    log_date_format: str = config.get('log_date_format')
    log_console_language: str = config.get('log_console_language')
    log_dir: str = config.get('log_dir', r'logs\%Y\%Y.%m')
    log_file: str = config.get('log_file', 'backup_log_%Y.%m.%d.log')
    
    if log_path is None:
        log_path = Path(log_dir, log_file)
    
    log_path = dt.now().strftime(str(log_path))
    
    try:
        log_dir = Path(log_path).parent
        if log_dir.exists() and not log_dir.is_dir():
            raise Exception(f'Path exists but is not a directory: {log_dir}')
        log_dir.mkdir(parents=True, exist_ok=True)
    except TypeError as e:
        logging.error(f'Variable must be a Path object or string, not "NoneType"! Error: {e}')
        return None
    except Exception as e:
        logging.error(f'Failed to create directory: {e}')
        return None
    
    try:
        logging_config.dictConfig({'version': 1, 'disable_existing_loggers': False,
            'formatters': {'standard': {'format': log_format_file, },
                'colored': {'()': ColoredFormatter, 'format': log_format_console, 'datefmt': log_date_format,
                    'reset': True, 'log_colors': {'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow', 'ERROR': 'red',
                        'CRITICAL': 'bold_red', }}}, 'handlers': {
                'console': {'class': 'logging.StreamHandler', 'formatter': 'colored', 'level': log_level_console, },
                'rotating_file': {'class': 'logging.handlers.RotatingFileHandler', 'formatter': 'standard',
                    'level': log_level_file, 'filename': log_path, 'maxBytes': 10 * 1024 * 1024, 'backupCount': 5, }, },
            'root': {'handlers': ['console', 'rotating_file'], 'level': log_level_root, }, })
    except Exception as e:
        logging.error(f'Error configuring logging: {e}')
        return None
    
    # log_ignore_list: List[str] = [
    #     # 'ignored element'
    # ]
    
    for logger_name in log_ignore_list:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    return log_console_language


def change_log_levels(console_level: str, file_level: Optional[str] = None) -> None:
    """
    Adjust the logging levels for console and file handlers.

    This function sets the logging level for the console output and optionally for the
    file output. If the file level is not specified, it defaults to the console level.

    :param console_level: The logging level for console output (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
    :param file_level: The logging level for file output (optional). If not provided, the console level will be used.

    :return: None
    """
    root_logger = logging.getLogger()
    if file_level is None:
        file_level = console_level
    
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            logging.info(f'Set logger level {console_level} to console.')
            handler.setLevel(console_level)
        elif isinstance(handler, logging.handlers.RotatingFileHandler):
            logging.info(f'Set logger level {file_level} to log file.')
            handler.setLevel(file_level)


setup_logger()

if __name__ == '__main__':
    log_levels: list = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    
    # Example on how to change log levels dynamically
    # This should be replaced with the actual logic for reading the new levels
    def test_console_level(console_level: str) -> None:
        new_console_level = console_level
        change_log_levels(new_console_level)
        
        # test
        logger = logging.getLogger(__name__)
        logger.debug('Log Level Debug!')
        logger.info('Log Level Info!')
        logger.warning('Log Level Warning!')
        logger.error('Log Level Error!')
        logger.critical('Log Level Critical!')
        logger.critical('')
    
    
    for level in log_levels:
        test_console_level(level)
