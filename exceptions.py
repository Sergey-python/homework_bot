from telegram.error import BadRequest, Unauthorized


class EnvVarDoesNotExist(Exception):
    """Ошибка, если переменные окружения не импортировались."""
    pass


class StatusCodeNot200(Exception):
    """Ошибка, если ответ сервера не 200."""

    def __init__(self, status_code, url):
        self.status_code = status_code
        self.url = url

    def __str__(self):
        return (
            f'По адрессу {self.url} статус код: '
            f'{self.status_code}, ожидался 200!'
        )


class ApiJsonKeyError(Exception):
    """Ошибка, если json не имеет требуемых данных."""
    pass


class ApiJsonTypeError(Exception):
    """Ошибка, если в json некорректные данные."""
    pass


class UnknownHomeworkStatus(Exception):
    """Ошибка, если у домашней работы неизвестный статус проверки."""
    pass


class TelegramTokenError(Exception):
    """Ошибка значения переменной окружения TELEGRAM_TOKEN."""
    def __str__(self):
        return 'Некорректный TELEGRAM_TOKEN!'


class TelegramChatIdError(Exception):
    """Ошибка значения переменной окружения TELEGRAM_CHAT_ID."""
    def __str__(self):
        return 'Некорректный TELEGRAM_CHAT_ID!'
