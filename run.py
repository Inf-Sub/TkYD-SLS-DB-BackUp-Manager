__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2025, [LegioNTeaM] InfSub'
__date__ = '2025/04/23'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'  # 'Production / Development'
__version__ = '1.0.3.2'


from asyncio import run as aio_run, CancelledError as aio_CancelledError

from backup import BackupManager
from server import ServerManager

from logger import logging, setup_logger


log_language = setup_logger()
logging = logging.getLogger(__name__)



async def execute():
    """
    Выполняет процесс резервного копирования, включая остановку и запуск сервера.

    Этот метод сначала останавливает сервер, затем выполняет резервное
    копирование, а после этого запускает сервер снова.
    """
    server_manager = ServerManager(language=log_language)
    backup_manager = BackupManager(language=log_language)
    
    try:
        logging.info(f"Stop Server.")
        await server_manager.stop_server()
        logging.info(f"Perform Copy Files.")
        await backup_manager.perform_copy_files()
        logging.info(f"Start Server.")
        # await server_manager.start_server()
        logging.info(f"Perform File Archiving.")
        await backup_manager.perform_file_archiving()
    except aio_CancelledError:
        logging.warning("Task was cancelled.")
    # finally:
    #     print("Cleanup actions.")


if __name__ == "__main__":
    # asyncio.run(backup_manager.execute())
    aio_run(execute())
