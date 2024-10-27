__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/27'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'  # 'Production / Development'
__version__ = '1.3.0'

import logging
import colorlog
from os import getenv, makedirs
from dotenv import load_dotenv
from os.path import join
from datetime import datetime


# Загрузка переменных из .env файла
load_dotenv()

LOG_FOLDER = getenv('LOG_FOLDER', 'Logs')
LOG_FILE_TEMPLATE = getenv('LOG_FILE_TEMPLATE', 'log_%Y-%m-%d.log')
# %(asctime)s - %(name)10s - %(levelname)8s - %(message)s
LOG_FORMAT = getenv('LOG_FORMAT', '%(asctime)s - %(levelname)8s - %(message)s')


# Вспомогательная функция для форматирования текущей даты
def get_formatted_date(format_str):
    return datetime.now().strftime(format_str)


# Декоратор для настройки и получения логгера
def with_logger_setup(func):
    def wrapper(*args, **kwargs):
        logger = configure_logging()
        return func(logger, *args, **kwargs)
    return wrapper


# Настройка логирования
def configure_logging():
    # Получаем директорию для логов из переменной окружения
    log_dir = join(get_formatted_date(LOG_FOLDER))

    # Убедитесь, что директория существует
    makedirs(log_dir, exist_ok=True)

    # Создаем имя файла лога с текущей датой
    log_file_name = f"{get_formatted_date(LOG_FILE_TEMPLATE)}"
    log_file_path = join(log_dir, log_file_name)

    # Создаем форматтер для логов с цветами
    color_formatter = colorlog.ColoredFormatter(
        f'%(log_color)s{LOG_FORMAT}',
        log_colors={
            'DEBUG': 'orange',
            'INFO': 'light_green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    # Настраиваем StreamHandler для вывода в консоль
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(color_formatter)

    # Настраиваем FileHandler для вывода в файл
    file_handler = logging.FileHandler(log_file_path)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)

    # Создаем логгер
    logger = logging.getLogger()

    # Устанавливаем уровень логирования
    logger.setLevel(logging.INFO)

    # Добавляем обработчики в логгер
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Пример использования декоратора
@with_logger_setup
def main(logger):
    logger.info("Программа запущена")


if __name__ == "__main__":
    # Вызов основного метода
    main()

