__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/26'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'  # 'Production / Development'
__version__ = '1.0.3'


# from sys import platform
from platform import system as pl_system
from subprocess import check_call, CalledProcessError
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


def get_executable_name(base_name: str) -> str:
    """Возвращает имя исполняемого файла в зависимости от платформы."""
    if pl_system() == "Windows":
        return f"{base_name}.exe"
    return base_name


def setup_and_run(venv_dir: str, command_list: list, executable: str = 'python') -> None:
    """Устанавливает зависимости из файла requirements.txt."""
    executable_path = get_executable_name(join(venv_dir, executable))

    logging.info("Устанавливаем зависимости...")
    try:
        check_call([executable_path] + command_list)
    except CalledProcessError as cpe:
        logging.error(f"Ошибка выполнения команды: {cpe}")
    except FileNotFoundError as fnf_e:
        logging.error(f"File '{executable_path}' not found: {fnf_e}")
    except Exception as e:
        logging.error(f"Неизвестная ошибка: {e}")


if __name__ == "__main__":
    venv_dir_name = VENV_PATH if not VENV_INDIVIDUAL else f'{VENV_PATH}_{getlogin()}'

    create_virtual_environment(venv_dir=venv_dir_name)
    venv_bin_path = join(venv_dir_name, 'Scripts')

    try:
        if exists(venv_bin_path):
            setup_and_run(venv_dir=venv_bin_path, command_list=['install', '-r', REQUIREMENTS_FILE], executable='pip')
            setup_and_run(venv_dir=venv_bin_path, command_list=['-m', 'pip', 'install', '--upgrade', 'pip'])
            setup_and_run(venv_dir=venv_bin_path, command_list=[MAIN_SCRIPT])
        else:
            logging.error(f"Directory '{venv_bin_path}' not found!")
    except KeyboardInterrupt:
        print("Execution was interrupted by the user.")

