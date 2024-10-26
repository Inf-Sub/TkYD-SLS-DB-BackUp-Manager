__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/26'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'  # 'Production / Development'
__version__ = '1.0.0'


from sys import platform
from subprocess import check_call
import logging
from os import getlogin
from os.path import exists, join
from venv import create as venv_create


VENV_PATH = '.venv'
VENV_INDIVIDUAL = False if getlogin().lower() == __maintainer__.lower() else True
REQUIREMENTS_FILE = 'requirements.txt'
MAIN_SCRIPT = "backup.py"


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def create_virtual_environment(venv_dir: str) -> None:
    """Создает виртуальное окружение в указанной директории."""
    if not exists(venv_dir):
        logging.info(f"Создаем виртуальное окружение в {venv_dir}...")
        venv_create(venv_dir, with_pip=True)
        # check_call(["python", "-m", "venv", venv_dir])
    else:
        logging.info(f"Виртуальное окружение уже существует в {venv_dir}.")


def install_dependencies(venv_dir: str, requirements_file: str) -> None:
    """Устанавливает зависимости из файла requirements.txt."""
    pip_executable = join(venv_dir, 'pip')
    if platform == "win32":
        pip_executable += ".exe"

    logging.info("Устанавливаем зависимости...")
    try:
        check_call([pip_executable, "install", "-r", requirements_file])
    except Exception as e:
        logging.error(f"File '{pip_executable}' not found: {e}")


def run_main_script(venv_dir: str, script_name: str) -> None:
    """Запускает основной скрипт main.py в виртуальном окружении."""
    python_executable = join(venv_dir, 'python')
    if platform == "win32":
        python_executable += ".exe"

    try:
        check_call([python_executable, "-m", "pip", "install", "--upgrade", "pip"])
    except Exception as e:
        logging.error(f"File '{python_executable}' not found: {e}")

    logging.info(f"Запускаем {script_name}...")
    try:
        check_call([python_executable, script_name])
    except Exception as e:
        logging.error(f"File '{python_executable}' not found: {e}")


if __name__ == "__main__":
    venv_dir_name = VENV_PATH if not VENV_INDIVIDUAL else f'{VENV_PATH}_{getlogin()}'

    create_virtual_environment(venv_dir=venv_dir_name)
    venv_bin_path = join(venv_dir_name, 'Scripts')

    if exists(venv_bin_path):
        install_dependencies(venv_dir=venv_bin_path, requirements_file=REQUIREMENTS_FILE)
        run_main_script(venv_dir=venv_bin_path, script_name=MAIN_SCRIPT)
    else:
        logging.error(f"Directory '{venv_bin_path}' not found!")



