__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2025/04/13'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'  # 'Production / Development'
__version__ = '1.0.2.5'

from asyncio import sleep as aio_sleep
from shutil import copy as sh_copy

from os import startfile as os_startfile
from os.path import basename as os_basename
from psutil import process_iter

from logger import logging, setup_logger
from config import Config


setup_logger()
logging = logging.getLogger(__name__)


class ServerManager:
    """
    Менеджер сервера.

    Этот класс управляет процессами запуска и остановки сервера, а также проверяет его состояние.

    :ivar env (dict): Словарь с конфигурацией сервера.
    :ivar server_dir (str): Директория, в которой находится сервер.
    :ivar server_process_name (str): Имя процесса сервера.
    :ivar server_start_file (str): Путь к файлу для запуска сервера.
    :ivar server_stop_file (str): Путь к файлу для остановки сервера.
    :ivar server_wait_seconds (int): Время ожидания сервера (сек).
    """

    def __init__(self, language: str = 'en'):
        """Инициализирует экземпляр ServerManager с настройками сервера."""
        self.env: dict = Config().get_config('server')

        self.server_dir: str = self.env.get('server_dir')
        self.server_start_file: str = self.env.get('server_start_file')
        self.server_stop_file: str = self.env.get('server_stop_file')
        self.server_process_name: str = self.env.get('server_process_name')
        self.server_wait_seconds: int = self.env.get('server_wait_seconds')
        self.language = language

    def __str__(self):
        """
        Возвращает строковое представление экземпляра ServerManager.

        :return: Строка, содержащая информацию о сервере, включая его директорию и имя процесса.
        """
        return f"ServerManager:\tserver_dir='{self.server_dir}'"

    def __repr__(self):
        """
        Возвращает формальное строковое представление экземпляра ServerManager.

        :return: Строка, предназначенная для разработки, включая все атрибуты экземпляра.
        """
        return (f"ServerManager:\n"
                # f"\tenv='{self.env}'\n"
                f"\tserver_dir='{self.server_dir}'\n"
                f"\tserver_process_name='{self.server_process_name}'\n"
                f"\tserver_start_file='{self.server_start_file}'\n"
                f"\tserver_stop_file='{self.server_stop_file}'\n"
                f"\tself.server_wait_seconds='{self.server_wait_seconds}'")
            
    async def start_server(self) -> bool:
        """
        Запускает сервер.

        Если запуск успешен, записывает информацию в лог.

        :return: True, если сервер запущен, иначе False.
        """
        if await self.is_server_running():
            logging.info("Server is already running.")
            return True
        
        try:
            os_startfile(self.server_start_file)
            logging.info("Server started.")
        except Exception as e:
            logging.error(f"Failed to start server: {e}")
            return False  # Возвращаем False, если запуск не удался
        
        # Ожидаем, пока сервер не запустится, с таймаутом в 10 секунд
        for _ in range(self.server_wait_seconds):
            if await self.is_server_running():
                logging.info("Server started successfully.")
                return True
            await aio_sleep(1)
        
        logging.warning("Server did not start in the expected time.")
        return False
    
    async def stop_server(self) -> bool:
        """
        Останавливает сервер, если он запущен.

        Если сервер работает, отправляет команду на остановку.

        :return: True, если сервер был остановлен, иначе False.
        """
        if not await self.is_server_running():
            logging.info("The server is already stopped.")
            return await self._kill_processes()
        
        try:
            sh_copy(self.server_stop_file, self.server_dir)
            logging.info("Server stop command issued.")
        except Exception as e:
            logging.error(f"Failed to issue server stop command: {e}")
            return False
        
        # Ожидание завершения процесса
        for _ in range(self.server_wait_seconds):
            if not await self.is_server_running():
                logging.info("Server stopped successfully.")
                return await self._kill_processes()
            await aio_sleep(1)
        
        logging.warning("Server did not stop in time, forcing termination.")
        return await self._kill_processes()
    
    async def is_server_running(self, process_name: str = None) -> bool:
        """
        Проверяет, работает ли процесс сервера.

        :param process_name: Имя процесса для проверки (по умолчанию используется имя процесса сервера).
        :return: True, если сервер запущен, иначе False.
        """
        process_name = process_name or self.server_process_name
        process = await self._find_process_by_name(process_name)
        
        if process:
            logging.info(f'Process {process_name} is running.')
            return True
        
        logging.info(f'Process {process_name} is not running.')
        return False

    @staticmethod
    async def _find_process_by_name(process_name: str):
        """
        Находит процесс по имени.

        :param process_name: Имя процесса для поиска.
        :return: Процесс, если найден; иначе None.
        """
        for process in process_iter(['name']):
            if process.info['name'] == process_name:
                return process
        return None
    
    async def _kill_process_by_name(self, process_name: str) -> None:
        """
        Завершает процесс по имени.

        :param process_name: Имя процесса, который необходимо завершить.
        """
        process = await self._find_process_by_name(process_name)
        
        if process:
            process.kill()
            logging.info(f'The process "{process_name}" is completed.')
        else:
            logging.info(f'The process "{process_name}" was not found.')
    
    async def _kill_processes(self) -> bool:
        """Убивает процесс сервера и его стартовый файл."""
        await self._kill_process_by_name(self.server_process_name)
        await self._kill_process_by_name(os_basename(self.server_start_file))
        return True


if __name__ == "__main__":
    from asyncio import run as aio_run, CancelledError as aio_CancelledError

    async def test():
        server_manager = ServerManager()
        print(f'{server_manager}')  # __str__
        print()
        print(f'{server_manager=}')  # __repr__

        try:
            logging.info(f"Start Server.")
            await server_manager.start_server()
            await aio_sleep(5)
            logging.info(f"Stop Server.")
            await server_manager.stop_server()
            # logging.info(f"Start Server.")
            # await server_manager.start_server()
        except aio_CancelledError:
            print("Task was cancelled.")
        # finally:
        #     print("Cleanup actions.")

    aio_run(test())