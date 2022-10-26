import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Union

import requests
import telegram
from dotenv import load_dotenv
from telegram.error import BadRequest, Unauthorized

from exceptions import (ApiJsonTypeError,
                        EnvVarDoesNotExist,
                        ResponseObjNotJson,
                        StatusCodeNot200,
                        TelegramChatIdError,
                        TelegramTokenError,
                        UnknownHomeworkStatus)

load_dotenv()

PRACTICUM_TOKEN: str = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def get_custom_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s, %(levelname)s, %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = get_custom_logger()


def check_correct_keys_and_value_types(key_type: dict, obj: dict) -> None:
    """Проверка содержимого объекта json."""
    for key, type in key_type.items():
        if key not in obj:
            raise KeyError(f'У json отсутствует ключ: {key}!')
        if not isinstance(obj[key], type):
            raise ApiJsonTypeError(
                f'У json c ключом {key} ожидался тип: {type},'
                f'но оказался: {type(obj[key])}!'
            )


def send_message(bot, message: str) -> None:
    """Отправка сообщения ботом."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Unauthorized:
        raise TelegramTokenError()
    except BadRequest:
        raise TelegramChatIdError()
    message = message if len(message) < 40 else message[:40] + '...'
    logger.info(f'Сообщение ({message}) успешно отправлено в телеграмм.')


def get_api_answer(current_timestamp: int) -> Union[dict, list]:
    """Запрос к API сервиса Практикум-Домашка."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    logger.debug(f'Сделан запрос к api по адрессу: {ENDPOINT}')

    if response.status_code != HTTPStatus.OK:
        raise StatusCodeNot200(response.status_code, ENDPOINT)
    try:
        response = response.json()
    except Exception:
        raise ResponseObjNotJson()
    return response


def check_response(response: Union[dict, list]) -> list:
    """Получение списка проверенных домашних работ."""
    if isinstance(response, list):
        response = response[0]
    key_type = {'homeworks': list, 'current_date': int}
    check_correct_keys_and_value_types(key_type, response)
    homeworks = response['homeworks']

    if not homeworks:
        logger.debug(
            f'Нет проверенных домашних работ за последние {RETRY_TIME} секунд.'
        )
    else:
        logger.debug('Получили список проверенных домашних работ.')
    return homeworks


def parse_status(homework: dict) -> str:
    """Получение строки сообщения об изменении статуса проверки д/з."""
    key_type = {'homework_name': str, 'status': str}
    check_correct_keys_and_value_types(key_type, homework)
    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_STATUSES:
        raise UnknownHomeworkStatus(
            f'Недокументированный статус домашней работы: {homework_status}!'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    logger.debug(f'Вердикт ревьюера: {verdict}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка корректного импорта переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    try:
        if not check_tokens():
            raise EnvVarDoesNotExist()
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        logger.info('Осуществлен запуск бота.')
        send_message(bot, 'Бот запущен!')
    except Exception as error:
        logger.critical(error)
        sys.exit()

    current_timestamp = int(time.time()) - RETRY_TIME
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            homeworks = check_response(response)

            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)
        except (
            KeyError,
            ApiJsonTypeError,
            StatusCodeNot200,
            UnknownHomeworkStatus,
            ResponseObjNotJson
        ) as error:
            message = f'Сбой программы: {error}'
            logger.error(error)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой программы, неизвестная ошибка: {error}'
            logger.error(error)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
