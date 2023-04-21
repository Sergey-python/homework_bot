## Проект «Homework bot»

### Описание
«КакДомашка-бот» — это телеграм-бот, который отслеживает статус домашней работы Яндекс-Практикума. При изменении статуса, он отправляет соответствующее сообщение в телеграм.

### Технологии
Python 3.7, Python-telegram-bot 13.7

<details>
<summary><h3>Как запустить проект</h3></summary>

- Клонировать репозиторий:

```
git clone git@github.com:Sergey-python/homework_bot.git
```

- Создать и активировать виртуальное окружение:

```
python -m venv venv

source venv/Scripts/activate
```

- Установить зависимости:

```
pip install -r requirements.txt
```

- Переменные окружения, используемые в проекте(для этого создайте и заполните файл .env):

```
PRACTICUM_TOKEN - токен профиля на Яндекс.Практикуме
TELEGRAM_TOKEN - токен телеграм-бота
TELEGRAM_CHAT_ID - свой ID в телеграме
```

- Запускаем файл на исполнение:

```
python homework.py
```

