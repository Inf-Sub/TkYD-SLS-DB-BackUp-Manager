# __author__ = 'InfSub'
# __contact__ = 'ADmin@TkYD.ru'
# __copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
# __date__ = '2025/06/01'
# __deprecated__ = False
# __email__ = 'ADmin@TkYD.ru'
# __maintainer__ = 'InfSub'
# __status__ = 'Production'  # 'Production / Development'
# __version__ = '1.0.5.0'

from asyncio import subprocess, create_subprocess_exec
from os import makedirs as os_makedirs, path as os_path, walk as os_walk, remove as os_remove
from os import stat as os_stat, utime as os_utime
from re import search as re_search, sub as re_sub
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED
from shutil import disk_usage as shutil_disk_usage
from aiofiles import open as aio_open
from datetime import datetime
from typing import Tuple, Optional, List, Dict, Any

from config import Config
from logger import logging, setup_logger


setup_logger()
logging = logging.getLogger(__name__)


# TODO: Проверить в чем проблема если в пути до файла базы данных присутствуют пробелы (или в имени БД).


class BackupManager:
    """
    Менеджер резервного копирования, который управляет процессом создания, хранения и удаления резервных копий файлов.

    :ivar _env (Dict[str, Any]): Конфигурационный словарь с параметрами для резервного копирования файлов.
    :ivar _files_dir (str): Директория с исходными файлами.
    :ivar _files_backup_dir (str): Директория для хранения резервных копий.
    :ivar _files_extensions (List[str]): Список расширений файлов для резервного копирования.
    :ivar _files_in_use_extensions (List[str]): Список расширений файлов, которые используются в данный момент.
    :ivar _files_ignore_backup_files (bool): Игнорировать файлы резервных копий (с датами в имени).
    :ivar _files_min_required_space_gb (float): Минимально необходимое свободное место на диске в Гб.
    :ivar _files_archive_format (str): Формат архивирования (например, zip, 7z).
    :ivar _files_7z_path (str): Путь к архиватору 7z.
    :ivar _hash_extension (Optional[str]): Расширение для хеш-файлов (например, ".md5" или None).
    :ivar _date_pattern (str): Регулярное выражение для поиска дат в именах файлов.
    :ivar _date_format (str): Формат даты для парсинга.
    :ivar _file_times (Dict[str, Dict[str, Optional[float]]]): Словарь с метаданными файлов.
    :ivar _metadata_date_format (str): Формат даты метаданных файла.
    # :ivar _modification_time (Dict[str, Optional[float]]): Словарь с временем последней модификации файлов. (deprecated)
    :ivar _language (str): Язык логов ("en", "ru" и т.д.).
    """
    
    def __init__(self, language: Optional[str] = 'en') -> None:
        """Инициализирует экземпляр BackupManager с настройками и конфигурацией."""
        self.env: Dict[str, Any] = Config().get_config('files')

        self._files_dir: str = self.env.get('files_dir')
        self._files_backup_dir: str = self.env.get('files_backup_dir')
        self._files_extensions: List[str] = self.env.get('files_extensions')
        self._files_in_use_extensions: List[str] = self.env.get('files_in_use_extensions')
        self._files_ignore_backup_files: bool = self.env.get('files_ignore_backup_files', False)
        self._files_min_required_space_gb: float = self.env.get('files_min_required_space_gb')
        self._files_archive_format: str = self.env.get('files_archive_format')
        self._files_7z_path: str = self.env.get('files_7z_path')
        # self._files_path_separator: str = self._env.get('files_path_separator')
        self._hash_extension: Optional[str] = None
        self._date_pattern: str = r'(_\d{4}\.\d{2}\.\d{2})'
        self._date_format: str = '%Y.%m.%d_%H.%M'
        self._file_times: Dict[str, Dict[str, Optional[float]]] = dict()
        # self._modification_time: Dict[str, Optional[float]] = dict()  # deprecated
        self._metadata_date_format: str = '%Y-%m-%d %H:%M:%S'
        self._language: str = language if isinstance(language, str) else 'en'
    
    # async def get_file_times(self, backup_file_path: str) -> Optional[float]:
    #     """
    #     Обновляет время последней модификации файла по заданному пути.
    #     Возвращает время модификации или None, если файл не найден.
    #     """
    #     try:
    #         file_name = os_path.basename(backup_file_path).upper()
    #         mtime = os_path.getmtime(backup_file_path)
    #         self._modification_time[file_name] = mtime
    #
    #         log_message = {
    #             'en': 'The time of modification of the file "{backup_file_path}" was received: "{time}".',
    #             'ru': 'Получено время модификации файла "{backup_file_path}": "{time}".',
    #         }
    #         logging.debug(log_message.get(self._language, 'en').format(
    #             backup_file_path=backup_file_path, time=datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')))
    #         return mtime
    #     except FileNotFoundError:
    #         # Не вносим изменений в словарь
    #         log_message = {
    #             'en': 'File not found: "{backup_file_path}". No data was added to "_modification_time".',
    #             'ru': 'Файл не найден: "{backup_file_path}". В переменную "_modification_time" ничего не добавлено.',
    #         }
    #         logging.warning(log_message.get(self._language, 'en').format(backup_file_path=backup_file_path))
    #         return None
    #     except Exception as e:
    #         # Не вносим изменений в словарь при ошибке
    #         log_message = {
    #             'en': 'Error getting modification time of file "{backup_file_path}": {error}',
    #             'ru': 'Ошибка при получении времени модификации файла "{backup_file_path}": {error}',
    #         }
    #         logging.error(log_message.get(self._language, 'en').format(backup_file_path=backup_file_path, error=e))
    #         return None
    
    async def get_file_times(self, file_path: str) -> None:
        """
        Обновляет и возвращает информацию о времени файла по заданному пути.
        
        :param file_path: Путь к файлу.
        """
        try:
            stat_info = os_stat(file_path)
            # Формируем словарь с нужными датами
            file_info = {
                'modification_time': datetime.fromtimestamp(stat_info.st_mtime),
                # 'creation_time': datetime.fromtimestamp(stat_info.st_ctime),
                'access_time': datetime.fromtimestamp(stat_info.st_atime),
            }
            self._file_times[file_path.upper()] = file_info
            
            log_message = {
                'en': 'Metadata from the file "{file_path}". '
                      'Time of the last modification: {mod_time}; Last access time: {acc_time}.',
                'ru': 'Получены метаданные из файла "{file_path}". '
                      'Время последней модификации: {mod_time}; Время последнего доступа: {acc_time}.',
            }
            logging.debug(
                log_message.get(self._language, 'en').format(
                    file_path=file_path,
                    mod_time=file_info['modification_time'].strftime(self._metadata_date_format),
                    # cre_time=file_info['creation_time'].strftime(self._metadata_date_format),
                    acc_time=file_info['access_time'].strftime(self._metadata_date_format),
                )
            )
        except FileNotFoundError:
            log_message = {
                'en': 'File not found:"{file_path}". No data was added to "_file_times".',
                'ru': 'Файл не найден: "{file_path}". В переменную "_file_times" ничего не добавлено.',
            }
            logging.warning(log_message.get(self._language, 'en').format(file_path=file_path))
        except Exception as e:
            log_message = {
                'en': 'Error getting file times of "{file_path}": {error}',
                'ru': 'Ошибка при получении временных меток файла "{file_path}": {error}',
            }
            logging.error(log_message.get(self._language, 'en').format(file_path=file_path, error=e))

    async def set_file_times(self, original_path: str, target_path: str, params: Optional[List[str]] = None) -> None:
        """
        Устанавливает параметры времени для файла по целевому пути на основе данных исходного файла.

        :param original_path: Путь к исходному файлу.
        :param target_path: Путь к целевому файлу.
        :param params: Список параметров, которые нужно установить ('modification_time', 'access_time').
        Если не указан, устанавливаются все.

        """
        if original_path.upper() not in self._file_times:
            log_message = {
                'en': 'No time data available for source file: {file_path}.',
                'ru': 'Нет данных о времени исходного файла: {file_path}.',
            }
            logging.error(log_message.get(self._language, 'en').format(file_path=original_path))
            await self.get_file_times(original_path)

        source_file_times = self._file_times[original_path.upper()]
        if params is None:
            params = ['modification_time', 'access_time']

        try:
            # Получаем текущие метки времени целевого файла
            await self.get_file_times(target_path)
            target_file_times = self._file_times[target_path.upper()]
            target_atime = target_file_times.get('access_time', None)
            target_mtime = target_file_times.get('modification_time', None)

            if 'access_time' in params:
                target_atime = source_file_times.get('access_time', target_atime).timestamp()
            if 'modification_time' in params:
                target_mtime = source_file_times.get('modification_time', target_mtime).timestamp()

            os_utime(target_path, times=(target_atime, target_mtime))

            self._file_times[target_path.upper()] = {
                'modification_time': source_file_times.get('modification_time', datetime.fromtimestamp(target_mtime)),
                # 'creation_time': source_times.get('creation_time', datetime.fromtimestamp(ctime)),
                'access_time': source_file_times.get('access_time', datetime.fromtimestamp(target_atime)),
            }
        except Exception as e:
            log_message = {
                'en': 'Error setting file times for "{target_path}": "{error}".',
                'ru': 'Ошибка установки времени файла для "{target_path}": "{error}".',
            }
            logging.error(log_message.get(self._language, 'en').format(target_path=target_path, error=e))

    async def perform_copy_files(self) -> None:
        copy_pattern = r'\s*[-—]\s*копия'

        # Обход всех файлов в указанной директории
        for root, _, files in os_walk(self._files_dir):
            # Фильтруем файлы по расширениям заранее
            filtered_files = [file for file in files if file.endswith(tuple(self._files_extensions))]
            
            for file in filtered_files:
                file_path = os_path.join(root, file)
                log_message = {
                    'en': 'Processing file path: "{file_path}". File: "{file}".',
                    'ru': 'Обработка пути к файлу: "{file_path}". Файл: "{file}".',
                }
                logging.info(log_message.get(self._language, 'en').format(file_path=file_path, file=file))
                
                if await self._check_file_in_use(file_path):
                    log_message = {
                        'en': 'File "{file_path}" is in use, skipping backup.',
                        'ru': 'Файл "{file_path}" используется, резервное копирование пропускается.',
                    }
                    logging.warning(log_message.get(self._language, 'en').format(file_path=file_path))
                    continue  # Пропускаем используемые в данный момент файлы
                
                filename_without_ext, file_modified_date, is_original = await self._get_backup_name_and_date(
                    file_path=file_path)
                log_message = {
                    'en': 'File is original (not a copy): "{is_original}". '
                          'Ignore backup files: "{ignore_backup}". File "{file_path}".',
                    'ru': 'Файл является оригиналом (не копией): "{is_original}". '
                          'Игнорировать файлы резервных копий: "{ignore_backup}". Файл "{file_path}".',
                }
                logging.info(log_message.get(self._language, 'en').format(
                    is_original=is_original, ignore_backup=self._files_ignore_backup_files, file_path=file_path))

                if not is_original and self._files_ignore_backup_files:
                    # Пропускаем резервные копии файлов БД (файлы с датой в имени)
                    log_message = {
                        'en': 'This file "{file_path}" is a backup, skipping backup.',
                        'ru': 'Этот файл "{file_path}" является резервной копией, резервное копирование пропускается.',
                    }
                    logging.warning(log_message.get(self._language, 'en').format(file_path=file_path))
                    continue
                
                # Очищаем имя файла от суффикса "копия", при его наличии
                clean_file_name = re_sub(copy_pattern, '', filename_without_ext)
                _, file_extension = os_path.splitext(file_path)
                backup_file_name = f'{clean_file_name}_{file_modified_date}{file_extension}'
                
                backup_directory = await self._prepare_backup_directory(unique_name=clean_file_name, file_path=file_path)
                backup_file_path = os_path.join(backup_directory, backup_file_name)
                await self._ensure_sufficient_space(backup_directory, file_path)
                
                # Копируем файл БД
                log_message = {
                    'en': 'Copy file: {file_path} to {backup_path}.',
                    'ru': 'Копируем файл: {file_path} в {backup_path}.',
                }
                logging.warning(log_message.get(self._language, 'en').format(
                    file_path=file_path, backup_path=backup_file_path))
                # Копируем файл в папку с архивами
                _ = await self._copy_file(file_path=file_path, backup_file_path=backup_file_path)
                
                if clean_file_name != filename_without_ext:
                    log_message = {
                        'en': 'The new file name "{file_path}" is not equal to the old "{file_name}". '
                              'Deleting file: "{file_path}".',
                        'ru': 'Новое имя файла "{file_path}" не равно старому "{file_name}". '
                              'Удаляем файл: "{file_path}".',
                    }
                    logging.warning(log_message.get(self._language, 'en').format(
                        clean_file_name=clean_file_name, file_path=file_path))
                    await self._delete_file(file_path)

        self._files_dir = self._files_backup_dir

    async def _check_file_in_use(self, db_path: str) -> bool:
        """
        Проверяет наличие активных файлов баз данных с заданными расширениями.

        :param db_path: Путь к базе данных.

        :return: True, если найдены активные файлы, иначе False.
        """
        for ext in self._files_in_use_extensions:
            if os_path.exists(db_path + ext):
                return True
        return False

    async def _get_backup_name_and_date(self, file_path: str) -> Tuple[str, str, bool]:
        """
        Извлекает имя файла без даты и дату модификации файла.

        :param file_path: Путь к файлу.
        :return: Кортеж, содержащий имя файла без даты, дату модификации в формате 'YYYY.MM.DD_HH.MM' и флаг,
                 указывающий, является ли файл оригинальным (без даты в имени).
        """
        date_pattern = self._date_pattern
        file_name = os_path.basename(file_path)
        
        log_message = {
            'en': 'Getting backup name and date for "{file_path}": {date_pattern}',
            'ru': 'Получение имени и даты резервной копии для "{file_path}": {date_pattern}',
        }
        logging.info(log_message.get(self._language, 'en').format(file_path=file_path, date_pattern=date_pattern))
    
        await self.get_file_times(file_path)

        modification_timestamp = self._file_times.get(file_path.upper(), {}).get('modification_time', None)
        modified_date = modification_timestamp.strftime(self._date_format)
        
        match = re_search(date_pattern, file_name)
        
        if not match:
            # file_name_without_date = file_name.rsplit('.', 1)[0]
            file_name_without_date, _ = os_path.splitext(file_name)
            is_original = True
            log_message = {
                'en': 'Date not found in file name: "{old_file_name}". New file name: "{new_file_name}".',
                'ru': 'Дата не найдена в имени файла: "{old_file_name}". Новое имя файла: "{new_file_name}".',
            }
            logging.info(log_message.get(self._language, 'en').format(
                old_file_name=file_name, new_file_name=file_name_without_date))
        else:
            file_name_without_date = file_name.split(match.group(0))[0]
            is_original = False
            log_message = {
                'en': 'Date found in file name: "{old_file_name}". File name without date: "{new_file_name}"',
                'ru': 'Дата найдена в имени файла: "{old_file_name}". Имя файла без даты: "{new_file_name}"',
            }
            logging.warning(log_message.get(self._language, 'en').format(
                old_file_name=file_name, new_file_name=file_name_without_date))
        
        return file_name_without_date, modified_date, is_original

    async def _prepare_backup_directory(self, unique_name: str, file_path: str) -> str:
        """
        Подготавливает директорию для резервной копии.

        :param unique_name: Уникальное имя файла для создания одноименной директории.
        :param file_path: Путь до файла.
        :return: Путь к директории, в которую будет сохранена резервная копия.
        """
        modification_timestamp = self._file_times.get(file_path.upper(), {}).get('modification_time', None)

        backup_path = os_path.join(
            self._files_backup_dir,
            unique_name,
            modification_timestamp.strftime('%Y'),
            modification_timestamp.strftime('%Y.%m'),
            # modification_timestamp.strftime('%Y.%m.%d')
        )
        log_message = {
            'en': 'Create directory: "{backup_path}".',
            'ru': 'Создаем каталог: "{backup_path}".',
        }
        logging.info(log_message.get(self._language, 'en').format(backup_path=backup_path))
        os_makedirs(backup_path, exist_ok=True)
        
        return backup_path

    async def _ensure_sufficient_space(self, backup_path: str, db_path: str) -> None:
        """
        Обеспечивает достаточное количество места для резервной копии, удаляя старые копии при необходимости.

        Этот метод проверяет, достаточно ли свободного места в директории резервной копии, и если места недостаточно,
        запускает процесс удаления самых старых резервных копий до тех пор, пока не будет обеспечено требуемое количество
        пространства. Это помогает предотвратить переполнение диска и гарантирует, что резервные копии могут быть
        созданы без ошибок.

        :param backup_path: Путь к директории резервной копии.
        :param db_path: Путь к базе данных.
        :raises Exception: В случае ошибки при удалении старых копий.
        """
        while not await self._has_sufficient_space(backup_path, db_path):
            await self._delete_oldest_backup(db_path)

    async def _copy_file(self, file_path: str, backup_file_path: str) -> str:
        """
        Копирует файл в директорию для бэкапа.

        Метод открывает указанный файл для чтения и копирует его содержимое в директорию резервного копирования.
        После успешного завершения операции возвращается путь к созданному резервному файлу. В процессе копирования
        записывается информационное сообщение в лог.

        :param file_path: Путь к исходному файлу, который необходимо скопировать.
        :param backup_file_path: Путь к директории, в которую будет скопирован файл.
        :return: Путь к созданному резервному файлу.
        :raises Exception: В случае ошибки при чтении или записи файла.
        """
        # Реализация копирования файла
        async with aio_open(file_path, 'rb') as src_file:
            async with aio_open(backup_file_path, 'wb') as dst_file:
                await dst_file.write(await src_file.read())
        
        # Установка времени последней модификации для нового файла
        # os_utime(backup_file_path, times=(stat_info.st_atime, mtime))
        await self.set_file_times(file_path, backup_file_path)
        
        log_message = {
            'en': 'File: "{file_path}" copied to "{backup_file_path}".',
            'ru': 'Файл: "{file_path}" скопирован в "{backup_file_path}".',
        }
        logging.info(log_message.get(self._language, 'en').format(
            file_path=file_path, backup_file_path=backup_file_path))
        return backup_file_path

    async def _delete_file(self, file_path: str) -> None:
        """
        Удаляет файл.

        Этот метод принимает путь к файлу и удаляет его из файловой системы. После успешного удаления записывается
        предупреждающее сообщение в лог, что позволяет отслеживать изменения в файловой системе.

        :param file_path: Путь к файлу, который необходимо удалить.
        :raises Exception: В случае ошибки при удалении файла.
        """
        try:
            os_remove(file_path)
            log_message = {
                'en': 'Successfully deleted: "{file_path}".',
                'ru': 'Успешно удалено: "{file_path}".'
            }
            logging.warning(log_message.get(self._language, 'en').format(file_path=file_path))
        except Exception as e:
            log_message = {
                'en': 'Error deleting backup "{file_path}": {error}.',
                'ru': 'Ошибка удаления резервной копии "{file_path}": {error}.',
            }
            logging.error(log_message.get(self._language, 'en').format(file_path=file_path, error=e))
            raise
    
    async def _has_sufficient_space(
            self, backup_path: str, file_path: str, min_required_space_gb: Optional[float] = None) -> bool:
        """
        Проверяет, достаточно ли свободного места на диске для резервной копии.
    
        Этот метод вычисляет доступное свободное место на диске, куда планируется сохранить резервную копию,
        и сравнивает его с размером файла, который нужно сохранить, а также с минимально необходимым пространством.
        Если свободного места недостаточно, метод возвращает False, что позволяет избежать ошибок при попытке
        сохранить резервную копию на диске с недостаточным пространством.
    
        :param backup_path: Путь к директории, в которую будет сохраняться резервная копия.
        :param file_path: Путь к файлу, размер которого необходимо учесть.
        :param min_required_space_gb: Минимально необходимое свободное место в гигабайтах. Если не указано,
        используется значение по умолчанию.
        :return: True, если свободного места достаточно, иначе False.
        :raises Exception: В случае ошибки при получении информации о дисковом пространстве или размере файла.
        """
        # Получаем информацию о свободном месте на диске
        free_space_gb = shutil_disk_usage(backup_path).free / (1024 ** 3)
        db_size_gb = os_path.getsize(file_path) / (1024 ** 3)
        
        if min_required_space_gb is None:
            min_required_space_gb = self._files_min_required_space_gb
        
        log_message = {
            'en': 'Free disk space: {free_space_gb:.2f} GB, Required size: {db_size_gb:.2f} GB, '
                  'Minimum required space: {min_required_space_gb:.2f} GB.',
            'ru': 'Свободное место на диске: {free_space_gb:.2f} ГБ, Требуемый размер: {db_size_gb:.2f} ГБ, '
                  'Минимально необходимое место: {min_required_space_gb:.2f} ГБ.',
        }
        logging.info(log_message.get(self._language, 'en').format(
            free_space_gb=free_space_gb, db_size_gb=db_size_gb, min_required_space_gb=min_required_space_gb))
        
        # Проверка, достаточно ли места для резервной копии с учетом минимально необходимого места
        has_sufficient_space = free_space_gb > (db_size_gb + min_required_space_gb)
        
        # Логируем результат проверки
        log_message = {
            'en': f'{"Sufficient" if {has_sufficient_space} else "Not enough"} space for backup',
            'ru': f'{"Достаточно" if {has_sufficient_space} else "Недостаточно"} места для резервной копии',
        }
        if has_sufficient_space:
            logging.info(log_message.get(self._language, 'en'))
        else:
            logging.warning(log_message.get(self._language, 'en'))
        
        return has_sufficient_space
    
    # async def _delete_oldest_backup(self, backup_file_path: str) -> None:
    #     """
    #     Удаляет самую старую резервную копию для указанного файла.
    #
    #     Этот метод ищет все резервные копии для заданного файла в директории
    #     резервных копий, определяет самую старую резервную копию и удаляет её.
    #     Это необходимо для управления пространством хранения и предотвращения
    #     переполнения диска.
    #
    #     :param backup_file_path: Путь к файлу, для которого нужно удалить резервную копию.
    #     :raises FileNotFoundError: Если резервные копии не найдены.
    #     :raises Exception: В случае ошибки при удалении резервной копии.
    #     """
    #     # Получаем директорию резервных копий
    #     backup_dir = self._get_backup_directory(backup_file_path)
    #
    #     # Получаем список всех резервных копий для данного файла
    #     backups: List[str] = []
    #     for dirpath, _, filenames in os_walk(backup_dir):
    #         for filename in filenames:
    #             if filename.startswith(os_path.basename(backup_file_path)):
    #                 backups.append(os_path.join(dirpath, filename))
    #
    #     if not backups:
    #         log_message = {
    #             'en': 'No backups found for "{backup_file_path}".',
    #             'ru': 'Резервные копии для "{backup_file_path}" не найдены.',
    #         }
    #         logging.error(log_message.get(self._language, 'en').format(backup_file_path=backup_file_path))
    #         raise FileNotFoundError(f'No backups found for "{backup_file_path}".')
    #
    #     # Находим самую старую резервную копию
    #     oldest_backup = min(backups, key=os_path.getctime)
    #
    #     log_message = {
    #         'en': 'Deleting oldest backup: "{oldest_backup}".',
    #         'ru': 'Удаление самой старой резервной копии: "{oldest_backup}".',
    #     }
    #     logging.warning(log_message.get(self._language, 'en').format(oldest_backup=oldest_backup))
    #
    #     await self._delete_file(oldest_backup)
    
    async def _delete_oldest_backup(self, backup_file_path: str, skip_conditions: List[str] = None) -> None:
        """
        Удаляет самую старую резервную копию для указанного файла.

        Этот метод ищет все резервные копии для заданного файла в директории
        резервных копий, определяет самую старую резервную копию и удаляет её.
        Это необходимо для управления пространством хранения и предотвращения
        переполнения диска.

        :param backup_file_path: Путь к файлу, для которого нужно удалить резервную копию.
        :param skip_conditions: Список условий для пропуска архивов.
        :raises FileNotFoundError: Если резервные копии не найдены.
        :raises Exception: В случае ошибки при удалении резервной копии.
        """
        # Получаем директорию резервных копий
        try:
            backup_dir = self._get_backup_directory(backup_file_path)
        except Exception as e:
            # Временно, пока метод не дописан и self._get_backup_directory метод не реализован
            logging.error(e)
            # raise e
            return
        
        # Получаем список всех резервных копий для данного файла
        backups: List[str] = []
        for dirpath, _, filenames in os_walk(backup_dir):
            for filename in filenames:
                if filename.startswith(os_path.basename(backup_file_path)):
                    # Проверяем условия для пропуска архива
                    if skip_conditions and any(condition in filename for condition in skip_conditions):
                        continue
                    backups.append(os_path.join(dirpath, filename))
        
        if not backups:
            log_message = {
                'en': 'No backups found for "{file_path}".',
                'ru': 'Резервные копии для "{file_path}" не найдены.',
            }
            logging.error(log_message.get(self._language, 'en').format(file_path=backup_file_path))
            raise FileNotFoundError(f'No backups found for "{backup_file_path}".')
        
        # Группируем резервные копии по уникальным именам файлов
        filename_groups = {}
        for backup in backups:
            base_filename = os_path.splitext(os_path.basename(backup))[0]
        # timestamp_match = re_search(r'_(\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2})$', base_filename)
        timestamp_match = re_search(self._date_pattern, base_filename)
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            timestamp = datetime.strptime(timestamp_str, self._date_format)
            if base_filename not in filename_groups:
                filename_groups[base_filename] = []
            filename_groups[base_filename].append((backup, timestamp))
    
        # Удаляем самые старые резервные копии, оставляя минимум одну
        for base_filename, backups in filename_groups.items():
            if len(backups) > 1:
                oldest_backup = min(backups, key=lambda x: x[1])[0]
                log_message = {
                    'en': 'Deleting oldest backup: "{oldest_backup}".',
                    'ru': 'Удаление самой старой резервной копии: "{oldest_backup}".',
                }
                logging.warning(log_message.get(self._language, 'en').format(oldest_backup=oldest_backup))
                await self._delete_file(oldest_backup)
            else:
                logging.info(f'Keeping backup: "{backups[0][0]}" for "{base_filename}".')
    
    async def perform_file_restoration(self, backup_file_path: str, restore_path: str) -> None:
        """
        Выполняет восстановление файлов из резервной копии.

        Этот метод принимает путь к архиву резервной копии и директорию, в которую
        будут восстановлены файлы. Он проверяет целостность архива и распаковывает
        файлы в указанную директорию. Если возникает ошибка, она будет обработана
        и залогирована.

        :param backup_file_path: Путь к архиву резервной копии, который необходимо восстановить.
        :param restore_path: Путь к директории, в которую будут восстановлены файлы.
        :raises Exception: В случае ошибки при восстановлении файлов из резервной копии.
        """
        # Логика восстановления файлов из архива будет реализована здесь.
        pass
    
    async def _check_backup_integrity(self, backup_file_path: str) -> bool:
        """
        Проверяет целостность резервной копии.

        Этот метод проверяет, не поврежден ли архив резервной копии, и может
        использовать различные методы проверки, такие как проверка контрольной суммы
        или проверка наличия необходимых файлов. Возвращает True, если резервная
        копия целостна, иначе False.
    
        :param backup_file_path: Путь к архиву резервной копии для проверки.
        :return: True, если резервная копия целостна, иначе False.
        """
        # Логика проверки целостности архива будет реализована здесь.
        pass

    async def perform_file_archiving(self) -> None:
        """
        Выполняет архивирование файлов в указанной директории.

        Этот метод проходит по всем файлам в заданной директории, фильтрует их по заданным
        расширениям и обрабатывает каждый файл для создания резервной копии. Если файл
        требует архивирования (например, если его хэш изменился), вызывается метод
        `_handle_backup_archive`.

        :raises Exception: В случае ошибки при обработке файлов или создании резервной копии
        """
        # Обход всех файлов в указанной директории
        for root, _, files in os_walk(self._files_dir):
            # Фильтруем файлы по расширениям заранее
            # filtered_files = [file for file in files if file.endswith(tuple(self._files_extensions))]
            # Фильтруем файлы по расширениям независимо от регистра
            filtered_files = [
                file for file in files if file.lower().endswith(tuple(ext.lower() for ext in self._files_extensions))]
            
            for file in filtered_files:
                backup_file_path = os_path.join(root, file)
                log_message = {
                    'en': 'Processing file path: "{file_path}". File: "{file}".',
                    'ru': 'Обработка пути к файлу: "{file_path}". Файл: "{file}".',
                }
                logging.info(log_message.get(self._language, 'en').format(file_path=backup_file_path, file=file))

                # Проверяем хэш и создаем архив, если необходимо
                # вынести в отдельный цикл по директории с бэкапами
                await self._handle_backup_archive(backup_file_path)
    
    async def _handle_backup_archive(self, backup_file_path: str) -> None:
        """
        Сравнивает хэши и создает архив, если резервной копии с таким хэшем еще нет.
    
        Этот метод проверяет, существует ли уже резервная копия для указанного файла,
        сравнивая его хэш с ранее сохраненными хэшами. Если резервная копия отсутствует,
        создается новый архив, а исходный файл удаляется.
    
        :param backup_file_path: Путь к файлу, для которого необходимо создать резервную копию.
        :raises Exception: В случае ошибки при создании архива или удалении файла.
        """
        if await self._should_skip_backup(backup_file_path):
            return  # Пропускаем, если резервная копия уже существует
        
        # Создаем архив
        await self._create_backup_archive(backup_file_path)
        # Удаляем файл после создания архива
        await self._delete_file(backup_file_path)

    async def _should_skip_backup(self, backup_file_path: str) -> bool:
        """
        Определяет, следует ли пропустить создание резервной копии.

        Этот метод вычисляет текущий хэш указанного файла и сравнивает его с хэшом,
        сохраненным в отдельном файле резервной копии. Если хэши совпадают, это
        означает, что файл не изменился с момента последнего резервирования, и
        создание новой резервной копии не требуется. В противном случае текущий хэш
        будет записан в файл, и резервное копирование будет выполнено.

        :param backup_file_path: Путь к файлу для резервного копирования / архивирования.
        :return: True, если резервная копия не требуется; False в противном случае.
        """
        file_name = os_path.basename(backup_file_path)

        await self.get_file_times(backup_file_path)
        
        current_hash, self._hash_extension = await self._calculate_file_hash(backup_file_path)
        hash_file_path = os_path.join(self._files_backup_dir, f'{file_name}.{self._hash_extension}')

        if os_path.exists(hash_file_path):
            async with aio_open(hash_file_path, 'r') as hash_file:
                last_hash = await hash_file.read()
                log_message = {
                    'en': 'Compare the current and last hashes of the file: "{file_path}". '
                          # 'Current hash: {current_hash}. Last hash: {last_hash}.'
                    ,
                    'ru': 'Сравниваем текущий и последний хэши файла: "{file_path}". '
                          # 'Текущий хэш: {current_hash}. Последний хэш: {last_hash}.'
                    ,
                }
                logging.info(log_message.get(self._language, 'en').format(
                    file_path=backup_file_path, current_hash=current_hash, last_hash=last_hash))
                if current_hash == last_hash:
                    log_message = {
                        'en': 'No changes in file: "{file_path}", skipping backup.',
                        'ru': 'Нет изменений в файле: "{file_path}", резервное копирование пропускается.',
                    }
                    logging.info(log_message.get(self._language, 'en').format(file_path=backup_file_path))

                    log_message = {
                        'en': 'Delete a copy of the file: "{file_path}".',
                        'ru': 'Удаляем копию файла: "{file_path}".',
                    }
                    logging.warning(log_message.get(self._language, 'en').format(file_path=backup_file_path))
                    await self._delete_file(backup_file_path)
                    
                    return True
        
        log_message = {
            'en': 'Write the file hash: "{file_path}", to the file: "{hash_file_path}".',
            'ru': 'Записываем хэш файла: "{file_path}", в файл: "{hash_file_path}".',
        }
        logging.info(log_message.get(self._language, 'en').format(file_path=backup_file_path, hash_file_path=hash_file_path))
        
        async with aio_open(hash_file_path, 'w') as hash_file:
            await hash_file.write(current_hash)
            
        # Устанавливаем дату хэш файла равной дате архивируемого файла
        modification_time = self._file_times.get(backup_file_path.upper(), {}).get('modification_time', None)
        # os_utime(hash_file_path, times=(modification_time, modification_time))
        await self.set_file_times(backup_file_path, hash_file_path)

        log_message = {
            'en': 'Install the date of the Hash file "{hash_file_path}" equal to the date "{time}" of the archive file '
                  '"{file_path}".',
            'ru': 'Устанавливаем дату хэш файла "{hash_file_path}" равной дате "{time}" архивируемого файла '
                  '"{file_path}".',
        }
        logging.info(log_message.get(self._language, 'en').format(
            hash_file_path=hash_file_path, time=modification_time, file_path=backup_file_path))

        return False

    async def _calculate_file_hash(self, file_path: str) -> tuple:
        """
        Вычисляет SHA-256 хэш для указанного файла.

        Этот метод открывает файл по указанному пути в бинарном режиме и вычисляет его
        SHA-256 хэш, читая файл по частям. Полученный хэш возвращается в виде шестнадцатеричной
        строки вместе с типом алгоритма хеширования.

        :param file_path: Путь к файлу, для которого необходимо вычислить хэш.
        :return: Кортеж, содержащий хэш файла в шестнадцатеричном формате и алгоритм хеширования.
        """
        hash_type = 'sha256'
        # log_message = {
        #     'en': 'Calculate "{hash_type}" hash: File: {basename}',
        #     'ru': 'Вычисляем хэш "{hash_type}": Файл: {basename}',
        # }
        # message = log_message.get(self._language, 'en').format(hash_type=hash_type, basename=os_path.basename(backup_file_path))
        # logging.info(message)

        hash_sha256 = sha256()
        async with aio_open(file_path, "rb") as f:
            while True:
                chunk = await f.read(4096)
                # chunk = await f.read(65536)  # Чтение файла порциями (alternative)
                if not chunk:
                    break
                hash_sha256.update(chunk)
        
        hash_digest = hash_sha256.hexdigest()
        log_message = {
            'en': 'Calculate "{hash_type}" hash: File: {basename} | Hash: {hash_digest}',
            'ru': 'Вычисляем хэш "{hash_type}": Файл: {basename} | Хэш: {hash_digest}',
        }
        logging.info(log_message.get(self._language, 'en').format(
            hash_type=hash_type, basename=os_path.basename(file_path), hash_digest=hash_digest))
        return hash_sha256.hexdigest(), hash_type

    async def _create_backup_archive(self, backup_file_path: str) -> None:
        """
        Создает архив с резервной копией файла.

        Этот метод принимает путь к файлу и создает его резервную копию в формате, указанном в параметрах. Если
        доступен 7z, используется этот формат, в противном случае создается zip-архив.

        :param backup_file_path: Путь до файла для резервного копирования.
        :raises Exception: В случае ошибки при создании архива.
        """
        backup_directory = os_path.dirname(backup_file_path)
        file_name = os_path.basename(backup_file_path)

        archive_format = self._files_archive_format.lower()
        archive_name = f"{file_name}.{archive_format}"
        archive_file_path = os_path.join(backup_directory, archive_name)

        try:
            if archive_format == '7z':
                # Проверяем наличие 7z.exe
                if not await self._is_7z_available():
                    log_message = {
                        'en': '7z executable not found, switching to zip format.',
                        'ru': 'Исполняемый файл 7z не найден, переключение на формат zip.', }
                    logging.warning(log_message.get(self._language, 'en'))
                    archive_format = 'zip'
                    archive_name = f"{file_name}.zip"
                    archive_file_path = os_path.join(backup_directory, archive_name)

            log_message = {
                'en': 'Creating archive: "{archive_path}" from file: "{file_path}".',
                'ru': 'Создаем архив: "{archive_path}" из файла: "{file_path}".',
            }
            logging.info(log_message.get(self._language, 'en').format(
                archive_path=archive_file_path, file_path=backup_file_path))

            if archive_format == 'zip':
                await self._create_zip_archive(backup_file_path, archive_file_path)
            elif archive_format == '7z':
                await self._create_7z_archive(backup_file_path, archive_file_path)

            # Устанавливаем дату архива равной дате архивируемого файла
            modification_time = self._file_times.get(backup_file_path.upper(), {}).get('modification_time', None)

            # os_utime(archive_path, times=(modification_time, modification_time))
            await self.set_file_times(backup_file_path, archive_file_path)

            log_message = {
                'en': 'Backup completed for "{file_path}".',
                'ru': 'Резервное копирование для "{file_path}" завершено.',
            }
            logging.info(log_message.get(self._language, 'en').format(file_path=backup_file_path))

        except Exception as e:
            log_message = {
                'en': 'Failed to backup "{file_path}": {error}.',
                'ru': 'Не удалось создать резервную копию "{file_path}": {error}.',
            }
            logging.error(log_message.get(self._language, 'en').format(file_path=backup_file_path, error=e))

            await self._delete_oldest_backup(backup_file_path)
    
    async def _is_7z_available(self) -> bool:
        """
        Проверяет наличие 7z.exe в системе.

        Этот метод запускает исполняемый файл 7z с параметром 'i' для проверки его доступности.
        Возвращает True, если 7z доступен, и False в противном случае.

        :return: True, если 7z доступен, иначе False.
        """
        try:
            # Запускаем 7z с параметром 'd' для проверки его доступности
            process = await create_subprocess_exec(
                f'{self._files_7z_path}',
                'i',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            await process.communicate()

            return process.returncode==0
        except FileNotFoundError:
            logging.error(f'FileNotFoundError')
            return False
        except Exception as e:
            log_message = {
                'en': 'Error while checking 7z availability: {error}.',
                'ru': 'Ошибка при проверке доступности 7z: {error}.',
            }
            logging.error(log_message.get(self._language, 'en').format(error=e))
            return False
    
    async def _create_7z_archive(self, backup_file_path: str, archive_path: str) -> None:
        """
        Создает архив 7z с помощью утилиты 7z.exe.

        Этот асинхронный метод вызывает внешнюю команду 7z для создания архива.
        Использует команду 'a' для добавления указанного файла в архив в формате 7z.

        :param backup_file_path: Путь к файлу, который необходимо архивировать.
        :param archive_path: Путь, по которому будет сохранен созданный архив.
        :raises Exception: Если при создании архива возникает ошибка.
        """
        process = await create_subprocess_exec(
            f'{self._files_7z_path}',
            'a', '-t7z', archive_path, backup_file_path,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # await process.communicate()
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logging.error(f'7z: {stdout=}; 7z: {stderr=}')
            raise Exception(f'Ошибка при создании архива: {stderr.decode().strip()}')

    @staticmethod
    async def _create_zip_archive(backup_file_path: str, archive_path: str) -> None:
        """
        Создает архив zip с помощью ZipFile.

        Этот метод принимает путь к файлу и путь, где будет сохранен zip-архив.
        Использует библиотеку ZipFile для создания архива с заданным сжатием.

        :param backup_file_path: Путь к файлу для архивирования.
        :param archive_path: Путь для сохранения созданного zip-архива.
        :raises Exception: В случае ошибки при создании zip-архива.
        """
        with ZipFile(archive_path, 'w', compression=ZIP_DEFLATED) as archive:
            archive.write(backup_file_path, os_path.basename(backup_file_path))









if __name__ == "__main__":
    pass
