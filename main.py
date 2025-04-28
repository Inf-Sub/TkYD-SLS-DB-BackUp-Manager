__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2025, [LegioNTeaM] InfSub'
__date__ = '2025/04/28'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'  # 'Production / Development'
__version__ = '1.7.3'


from sys import platform
from subprocess import check_call
import logging
from os import getlogin
from os.path import exists, join
from venv import create as venv_create


MAIN_SCRIPT = 'run'
REQUIREMENTS_FILE = 'requirements.txt'
VENV_PATH = '.venv'
VENV_INDIVIDUAL = False if getlogin().lower() == __maintainer__.lower() else True
LOG_FORMAT = '%(filename)s:%(lineno)d\n%(asctime)-20s| %(levelname)-8s| %(name)-20s\t| %(funcName)-28s| %(message)s'
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
        'en': 'Installing dependencies (requirements)...',
        'ru': 'Устанавливаем зависимости...',
    },
    'run_script': {
        'en': f'Running script "{{file}}"...',
        'ru': f'Запускаем скрипт "{{file}}"...',
    },
    'task_cancelled': {
        'en': 'Task was cancelled.',
        'ru': 'Задание отменено',
    },
    'dir_not_found': {
        'en': f'Directory "{{path}}" not found!', 'ru':
        f'Каталог "{{path}}" не найден!',
    },
    'file_not_found': {
        'en': f'File "{{file}}" not found: {{error}}.',
        'ru': f'Файл "{{file}}" не найден: {{error}}.',
    },
}

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT
)


def create_virtual_environment(venv_dir: str) -> None:
    """Создает виртуальное окружение в указанной директории."""
    if not exists(venv_dir):
        logging.info(LOG_MESSAGE.get('venv_create').get(LOG_LANGUAGE, 'en').format(path=venv_dir))
        venv_create(venv_dir, with_pip=True)
        # check_call(["python", "-m", "venv", venv_dir])
    else:
        logging.warning(LOG_MESSAGE.get('venv_exists').get(LOG_LANGUAGE, 'en').format(path=venv_dir))


def install_dependencies(venv_dir: str, requirements_file: str) -> None:
    """Устанавливает зависимости из файла requirements.txt."""
    pip_executable = join(venv_dir, 'pip')
    if platform == "win32":
        pip_executable += ".exe"

    logging.info(LOG_MESSAGE.get('requirements').get(LOG_LANGUAGE, 'en'))
    
    try:
        check_call([pip_executable, "install", "-r", requirements_file])
    except Exception as e:
        logging.error(LOG_MESSAGE.get('file_not_found').get(LOG_LANGUAGE, 'en').format(file=pip_executable, error=e))


def run_main_script(venv_dir: str, script_name: str) -> None:
    """Запускает основной скрипт проекта в виртуальном окружении."""
    python_executable = join(venv_dir, 'python')
    if platform == "win32":
        python_executable += ".exe"

    try:
        check_call([python_executable, "-m", "pip", "install", "--upgrade", "pip"])
    except Exception as e:
        logging.error(LOG_MESSAGE.get('file_not_found').get(LOG_LANGUAGE, 'en').format(file=python_executable, error=e))

    try:
        logging.info(LOG_MESSAGE.get('run_script').get(LOG_LANGUAGE, 'en').format(file=script_name))
        check_call([python_executable, script_name])
    except KeyboardInterrupt:
        logging.error(LOG_MESSAGE.get('task_cancelled').get(LOG_LANGUAGE, 'en'))
    except Exception as e:
        logging.error(LOG_MESSAGE.get('file_not_found').get(LOG_LANGUAGE, 'en').format(file=python_executable, error=e))
    # finally:
    #     print("Cleanup actions.")
        
def create_venv() -> None:
    venv_dir_name = VENV_PATH if not VENV_INDIVIDUAL else f'{VENV_PATH}_{getlogin()}'

    create_virtual_environment(venv_dir=venv_dir_name)
    venv_bin_path = join(venv_dir_name, 'Scripts')

    if exists(venv_bin_path):
        install_dependencies(venv_dir=venv_bin_path, requirements_file=REQUIREMENTS_FILE)
        run_main_script(venv_dir=venv_bin_path, script_name=f'{MAIN_SCRIPT}.py')
    else:
        logging.error(LOG_MESSAGE.get('dir_not_found').get(LOG_LANGUAGE, 'en').format(path=venv_bin_path))


if __name__ == "__main__":
    create_venv()
