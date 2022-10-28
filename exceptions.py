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


class UnknownHomeworkStatus(Exception):
    """Ошибка, если у домашней работы неизвестный статус проверки."""
    pass


class TelegramTokenError(Exception):
    """Ошибка значения переменной окружения TELEGRAM_TOKEN."""

    def __str__(self):
        return super().__str__() or 'Некорректный TELEGRAM_TOKEN!'


class TelegramChatIdError(Exception):
    """Ошибка значения переменной окружения TELEGRAM_CHAT_ID."""

    def __str__(self):
        return super().__str__() or 'Некорректный TELEGRAM_CHAT_ID!'


class BotSendMessageError(Exception):
    """Ошибка во время отправки сообщения в телеграм."""

    def __init__(self, error):
        self.error = error

    def __str__(self):
        return ('Во время отправки сообщения в телеграм произошел сбой! '
                f'Ошибка: {self.error}')


class ResponseObjNotJson(Exception):
    """Ошибка, если в ответе от сервиса пришел не json."""

    def __str__(self):
        return super().__str__() or 'В ответе от сервиса пришел не json.'
