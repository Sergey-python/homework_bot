from http import HTTPStatus
import logging
import os
import sys
import time

from dotenv import load_dotenv
import requests
import telegram
from telegram.error import Unauthorized, BadRequest

from exceptions import (ApiJsonKeyError,
                        ApiJsonTypeError,
                        EnvVarDoesNotExist,
                        StatusCodeNot200,
                        UnknownHomeworkStatus,
                        TelegramTokenError,
                        TelegramChatIdError)


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


def check_correct_obj_keys_and_valuse(json_key_type: dict, obj: dict) -> None:
    """Проверка содержимого объекта json."""
    for key, type in json_key_type.items():
        if key not in obj:
            raise ApiJsonKeyError(f'У json отсутствует ключ: {key}!')
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
    logger.info(f'Сообщение ({message[:40]}...) успешно отправлено.')


def get_api_answer(current_timestamp: int) -> dict:
    """Запрос к API сервиса Практикум-Домашка."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        raise StatusCodeNot200(response.status_code, ENDPOINT)
    response = response.json()
    if isinstance(response, list):
        response = response[0]
    return response


def check_response(response: dict) -> list:
    """Проверка содержимого объекта json из ответа сервиса."""
    json_key_type = {'homeworks': list, 'current_date': int}
    check_correct_obj_keys_and_valuse(json_key_type, response)
    homeworks = response['homeworks']
    if len(homeworks) == 0:
        logger.debug(
            f'За последние {RETRY_TIME} секунд, статус домашних работ '
            'не изменился!'
        )
    return homeworks


def parse_status(homework: dict) -> str:
    """Получение строки сообщения, если изменился статус проверки д/з."""
    # json_key_type = {'homework_name': str, 'status': str}
    # check_correct_obj_keys_and_valuse(json_key_type, homework)
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise UnknownHomeworkStatus(
            f'Недокументированный статус домашней работы: {homework_status}!'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка корректного импорта переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    try:
        if not check_tokens():
            raise EnvVarDoesNotExist(
                'Проверьте существование переменных окружения!'
            )
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        logger.info('Осуществлен запуск бота.')
        send_message(bot, 'Бот запущен!')
    except (
        EnvVarDoesNotExist,
        TelegramTokenError,
        TelegramChatIdError
    ) as error:
        logger.critical(error)
        sys.exit()
    except Exception as error:
        logger.critical(error)
        sys.exit()

    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)

            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)
            current_timestamp = response['current_date']

        except (
            ApiJsonKeyError,
            ApiJsonTypeError,
            StatusCodeNot200,
            UnknownHomeworkStatus
        ) as error:
            logger.error(error)
            send_message(bot, error)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(error)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s, %(levelname)s, %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    main()
