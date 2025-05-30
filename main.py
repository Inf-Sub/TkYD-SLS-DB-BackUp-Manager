__author__ = 'InfSub'
__contact__ = 'https:/t.me/InfSub'
__copyright__ = 'Copyright (C) 2025, [LegioNTeaM] InfSub'
__date__ = '2025/04/30'
__deprecated__ = False
__maintainer__ = 'InfSub'
__status__ = 'Production'  # 'Production / Development'
__version__ = '1.7.6'

from sys import platform
from subprocess import check_call
import logging
from os import getlogin
from os.path import exists, join as os_join
from venv import create as venv_create

# Константы
MAIN_SCRIPT = "run"
REQUIREMENTS_FILE = 'requirements.txt'
VENV_PATH = '.venv'
LOG_FORMAT = '%(filename)s:%(lineno)d\n%(asctime)-20s| %(levelname)-8s| %(name)-10s| %(funcName)-27s| %(message)s'
LOG_DATE_FORMAT = '%Y.%m.%d %H:%M:%S'
LOG_LANGUAGE = 'en'  # en / ru
LOG_MESSAGE = {
    'venv_create': {
        'en': f'Creating a virtual environment in directory "{{path}}"...',
        'ru': f'Создаем виртуальное окружение в каталоге "{{path}}"...',
    },
    'venv_exists': {
        'en': f'Virtual environment already exists in directory "{{path}}".',
        'ru': f'Виртуальное окружение уже существует в каталоге "{{path}}".',
    },
    'requirements': {
        'en': 'Installing dependencies (requirements)...', 'ru': 'Устанавливаем зависимости...',
    },
    'run_script': {
        'en': f'Running script "{{file}}"...', 'ru': f'Запускаем скрипт "{{file}}"...',
    },
    'task_cancelled': {
        'en': 'Task was cancelled.', 'ru': 'Задание отменено',
    },
    'dir_not_found': {
        'en': f'Directory "{{path}}" not found!', 'ru': f'Каталог "{{path}}" не найден!',
    },
    'file_not_found': {
        'en': f'File "{{file}}" not found: {{error}}.',
        'ru': f'Файл "{{file}}" не найден: {{error}}.',
    },
}

# Настройка логирования
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)


class VirtualEnvironmentManager:
    def __init__(self, venv_path: str, individual: bool = True) -> None:
        self.venv_path = venv_path if not individual else f'{venv_path}_{getlogin()}'
    
    def create_virtual_environment(self) -> None:
        """Создает виртуальное окружение в указанной директории."""
        if not exists(self.venv_path):
            logging.info(LOG_MESSAGE['venv_create'][LOG_LANGUAGE].format(path=self.venv_path))
            venv_create(self.venv_path, with_pip=True)
        else:
            logging.warning(LOG_MESSAGE['venv_exists'][LOG_LANGUAGE].format(path=self.venv_path))
    
    def install_dependencies(self) -> None:
        """Устанавливает зависимости из файла requirements.txt."""
        pip_executable = os_join(
            self.venv_path, 'Scripts', 'pip') if platform == "win32" else os_join(self.venv_path, 'bin', 'pip')
        
        logging.info(LOG_MESSAGE['requirements'][LOG_LANGUAGE])
        
        try:
            check_call([pip_executable, "install", "-r", REQUIREMENTS_FILE])
        except Exception as e:
            logging.error(LOG_MESSAGE['file_not_found'][LOG_LANGUAGE].format(file=pip_executable, error=e))
    
    def run_main_script(self) -> None:
        """Запускает основной скрипт проекта в виртуальном окружении."""
        python_executable = os_join(self.venv_path, 'Scripts', 'python') if platform == "win32" else os_join(
            self.venv_path, 'bin', 'python')
        
        try:
            check_call([python_executable, "-m", "pip", "install", "--upgrade", "pip"])
            logging.info(LOG_MESSAGE['run_script'][LOG_LANGUAGE].format(file=MAIN_SCRIPT))
            check_call([python_executable, f'{MAIN_SCRIPT}.py'])
        except KeyboardInterrupt:
            logging.error(LOG_MESSAGE['task_cancelled'][LOG_LANGUAGE])
        except Exception as e:
            logging.error(LOG_MESSAGE['file_not_found'][LOG_LANGUAGE].format(file=python_executable, error=e))
    
    def setup(self) -> None:
        """Запускает процесс создания виртуального окружения и установки зависимостей."""
        self.create_virtual_environment()
        if exists(os_join(self.venv_path, 'Scripts')) or exists(os_join(self.venv_path, 'bin')):
            self.install_dependencies()
            self.run_main_script()
        else:
            logging.error(
                LOG_MESSAGE['file_not_found'][LOG_LANGUAGE].format(file=self.venv_path, error='Directory not found'))


if __name__ == "__main__":
    VENV_INDIVIDUAL = False if getlogin().lower() == __maintainer__.lower() else True
    manager = VirtualEnvironmentManager(VENV_PATH, VENV_INDIVIDUAL)
    manager.setup()
