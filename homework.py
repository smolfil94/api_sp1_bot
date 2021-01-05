import os
import time

import logging
import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {
    'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
}

VERDICTS_OF_STATUS = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
}
STATUS_ERROR = 'Получен не ожидаемый статус работы: {status}'
ANSWER = 'У вас проверили работу "{name}" от {date}!\n\n{verdict}'
REQUEST_ERROR = ('Ошибка запроса по адресу: {url}, параметры: {params}, '
                 '{headers}. Текст ошибки: {e}')
CONNECTION_ERROR = ('Попытка обращения к серверу: {url} имеет ошибку {error}.'
                    'Параметры: {params}')
CODE_ERROR = ('Попытка обращения к серверу: {url}, параметры: {params}. '
              'В результате присутствует {code}. Ошибка {error}.')
BOT_ERROR = 'Бот столкнулся с ошибкой: {error}'


def parse_homework_status(homework):
    status = homework['status']
    if status not in VERDICTS_OF_STATUS:
        raise ValueError(STATUS_ERROR.format(status=status))
    return ANSWER.format(name=homework['homework_name'],
                         verdict=VERDICTS_OF_STATUS[status],
                         date=homework['date_updated'])


def get_homework_statuses(current_timestamp):
    params = {
        'from_date': current_timestamp
    }
    data_source = dict(url=URL, headers=HEADERS, params=params)
    try:
        response = requests.get(**data_source)
    except requests.exceptions.RequestException:
        raise requests.exceptions.RequestException(REQUEST_ERROR.format(
            url=URL,
            params=params,
            headers=HEADERS,
            error=requests.exceptions.ConnectionError
        ))
    json_response = response.json()
    if 'error' in json_response:
        raise ValueError(CONNECTION_ERROR.format(
            error=json_response['error']['error'],
            **data_source
        ))
    if 'code' in json_response:
        raise ValueError(CODE_ERROR.format(
            code=json_response['code'],
            error=json_response['message'],
            **data_source
        ))
    return json_response


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                (send_message(parse_homework_status
                              (new_homework.get('homeworks')[0]), bot_client))
            current_timestamp = (new_homework.get('current_date',
                                                  current_timestamp))
            time.sleep(1200)  # опрашивать раз в пять минут
        except Exception as e:
            logging.error(BOT_ERROR.format(error=e))
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(
        filename=__file__ + '.log',
        format='%(asctime)s %(funcName)s %(message)s'
    )
    main()
