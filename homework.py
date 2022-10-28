from json import JSONDecodeError
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

from exceptions import (ResponseObjNotJson,
                        StatusCodeNot200,
                        TelegramChatIdError,
                        TelegramTokenError,
                        UnknownHomeworkStatus,
                        BotSendMessageError)

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
    """Получение кастомного логгера."""
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


def send_message(bot, message: str) -> None:
    """Отправка сообщения ботом."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Unauthorized:
        raise TelegramTokenError()
    except BadRequest:
        raise TelegramChatIdError()
    except Exception as error:
        raise BotSendMessageError(error)
    message = message[:40] + (message[40:] and '...')
    logger.info(f'Сообщение ({message}) успешно отправлено в телеграмм.')


def get_api_answer(current_timestamp: int) -> Union[dict, list]:
    """Запрос к API сервиса Практикум-Домашка."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    logger.debug(f'Делаем запрос к api по адрессу: {ENDPOINT}')
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    logger.debug('Получили ответ от сервера.')

    if response.status_code != HTTPStatus.OK:
        raise StatusCodeNot200(response.status_code, ENDPOINT)
    try:
        response = response.json()
    except JSONDecodeError:
        raise ResponseObjNotJson()
    return response


def check_response(response: Union[dict, list]) -> list:
    """Получение списка проверенных домашних работ."""
    try:
        homeworks = response['homeworks']
        current_date = response['current_date']
    except KeyError as error:
        raise KeyError(f'У объекта json отсутствует ключ: {error.args[0]}!')
    except TypeError:
        raise TypeError('Пришли некорректные данные от api.')

    if not isinstance(homeworks, list):
        raise TypeError('У объекта json у ключа homeworks неверный тип!')
    if not isinstance(current_date, int):
        raise TypeError('У объекта json у ключа current_date неверный тип!')

    if not homeworks:
        logger.debug(
            f'Нет проверенных домашних работ за последние {RETRY_TIME} секунд.'
        )
    else:
        logger.debug('Получили список проверенных домашних работ.')
    return homeworks


def parse_status(homework: dict) -> str:
    """Получение строки сообщения об изменении статуса проверки д/з."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
    except KeyError as error:
        raise KeyError(f'У объекта json отсутствует ключ: {error.args[0]}!')
    except TypeError:
        raise TypeError('Пришли некорректные данные от api.')

    if not isinstance(homework_name, str):
        raise TypeError('У объекта json у ключа homework_name неверный тип!')
    if not isinstance(homework_status, str):
        raise TypeError('У объекта json у ключа status неверный тип!')

    if homework_status not in HOMEWORK_STATUSES:
        raise UnknownHomeworkStatus(
            f'Недокументированный статус домашней работы: {homework_status}!'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    logger.debug(message)
    return message


def check_tokens() -> bool:
    """Проверка корректного импорта переменных окружения."""
    logger.debug('Проверяется импорт переменных окружения.')
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Проверьте наличие переменных окружения!')
        sys.exit()
    logger.debug('Переменные окружения успешно импортированны.')

    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        logger.info('Осуществлен запуск бота.')
        send_message(bot, 'Бот запущен!')
    except BotSendMessageError as error:
        logger.error(error)
    except Exception as error:
        logger.critical(error)
        sys.exit()

    current_timestamp = int(time.time()) - RETRY_TIME
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)

            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой программы: {error}'
            logger.error(error)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
