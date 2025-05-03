__author__ = 'InfSub'
__contact__ = 'https:/t.me/InfSub'
__copyright__ = 'Copyright (C) 2025, [LegioNTeaM] InfSub'
__date__ = '2025/05/01'
__deprecated__ = False
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '0.0.4'

# try:
#     from config import Config
#     print('Модуль "config" успешно импортирован.')
# except ModuleNotFoundError:
#     print('Ошибка: Модуль "config" не найден.')
# except ImportError as e:
#     print(f'Ошибка импорта: {e}')
# import os
# from dotenv import load_dotenv
#
# # Загружаем переменные окружения из .env файла
# load_dotenv()

from typing import Dict, Optional, Any
from inspect import currentframe

from config import Config
from logger import logging

logging = logging.getLogger(__name__)


class MessageManager:
    def __init__(self, default_language: str = 'en') -> None:
        """
        Инициализирует менеджер сообщений с заданным языком по умолчанию.

        :param default_language: Язык по умолчанию для получения сообщений (по умолчанию 'en').
        """
        self.default_language = default_language
        self.messages = self._load_messages()
        
        # Получаем язык из переменных окружения, если он задан
        env_language: str = Config().get_config('msg').get('log_console_language', 'en')
        if env_language in self.messages:
            self.default_language = env_language
    
    @staticmethod
    def _load_messages() -> Dict[str, Dict[str, str]]:
        """
        Загружает базовые сообщения для поддержки разных языков.

        :return: Словарь с сообщениями для каждого языка.
        """
        return {'en': {'greeting': "Hello, {name}!", 'farewell': "Goodbye, {name}!",
            'error': "An error occurred: {error_message}", },
            'ru': {'greeting': "Здравствуйте, {name}!", 'farewell': "До свидания, {name}!",
                'error': "Произошла ошибка: {error_message}", }, }
    
    def set_messages(self, new_messages: Dict[str, Dict[str, str]], source_class: Optional[str] = None,
            source_method: Optional[str] = None) -> None:
        """
        Добавляет новые сообщения в существующий словарь, избегая конфликтов.

        :param new_messages: Словарь новых сообщений для добавления.
        :param source_class: Имя класса, из которого добавляются сообщения (по умолчанию None).
        :param source_method: Имя метода, из которого добавляются сообщения (по умолчанию None).
        """
        if source_class is None or source_method is None:
            # Получаем стек вызовов
            frame = currentframe().f_back  # Получаем фрейм предыдущего вызова
            if source_class is None:
                source_class = frame.f_locals['self'].__class__.__name__  # Получаем имя класса
                logging.debug(f'Called from class: {source_class}.')
            if source_method is None:
                source_method = frame.f_code.co_name  # Получаем имя вызывающего метода
                logging.debug(f'Called from method: {source_class}.{source_method}.')

        for lang, messages in new_messages.items():
            if lang not in self.messages:
                self.messages[lang] = {}
            
            for key, message in messages.items():
                # Создаем уникальный ключ с префиксом класса и метода
                prefixed_key = f'{source_class}|{source_method}|{key}' if source_class and source_method else key
                
                if prefixed_key not in self.messages[lang]:
                    self.messages[lang][prefixed_key] = message
                else:
                    logging.debug(
                        f'Conflict for key "{key}" from "{source_class}.{source_method}". Original message will be kept.')
    
    def get_message(self, key: str, **kwargs: Any) -> Optional[str]:
        """
        Получает сообщение по ключу и подставляет значения.

        :param key: Ключ сообщения.
        :param kwargs: Значения для подстановки в сообщение.
        :return: Отформатированное сообщение или None, если ключ не найден.
        """
        language_messages = self.messages.get(self.default_language)
        if language_messages:
            message_template = language_messages.get(key)
            if message_template:
                return message_template.format(**kwargs)
            else:
                error_message = f'Message key "{key}" not found in language "{self.default_language}".'
                logging.error(error_message)
                # raise KeyError(error_message)
                return None
        else:
            error_message = f'Language "{self.default_language}" is not supported.'
            logging.error(error_message)
            # raise ValueError(error_message)
            return None


if __name__ == "__main__":
    import inspect
    
    
    class MessageApp:
        def __init__(self):
            self._class_name: str = __class__.__name__
            self._method_name: Optional[str] = None
            self._message_manager = MessageManager()
        
        def setup_messages(self):
            self._method_name = inspect.currentframe().f_code.co_name
            
            # Новые сообщения для добавления
            additional_messages = {'en': {'custom_greeting': "Welcome to our application, {name}!",
                'custom_farewell': "Thank you for using our application, {name}!", # Добавлено для английского языка
            }, 'ru': {'custom_farewell': "Спасибо за использование нашего приложения, {name}!", }, }
            
            self._message_manager.set_messages(additional_messages, source_class=self._class_name,
                source_method=self._method_name)
            
            # print(
            #     f'{MessageApp.__name__=}',
            #     # f'{self._message_manager.__name__=}',
            #     f'{self.setup_messages.__name__=}',
            #     f'{self._message_manager.__class__.__name__=}',
            #     sep='\n'
            # )

        def display_messages(self, name):
            greeting_message = self._message_manager.get_message('greeting', name=name)
            logging.info(greeting_message)  # Вывод: Здравствуйте, Иван!
            
            custom_greeting_message = self._message_manager.get_message(
                f'{self._class_name}_{self._method_name}_custom_greeting', name=name)
            logging.info(custom_greeting_message)  # Вывод: Welcome to our application, Иван!
            
            error_message = self._message_manager.get_message('error', error_message='Файл не найден')
            logging.info(error_message)  # Вывод: Произошла ошибка: Файл не найден
            
            custom_farewell_message = self._message_manager.get_message(
                f'{self._class_name}_{self._method_name}_custom_farewell', name=name)
            logging.info(custom_farewell_message)  # Вывод: Thank you for using our application, Иван!
    
    
    app = MessageApp()
    app.setup_messages()
    app.display_messages(name='Иван')
