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
REQUEST_ERROR = ('Ошибка запроса по адресу: {url}, параметры: {params}, '
                 '{headers}. Текст ошибки: {e}')
BAD_STATUS = ('Попытка обращения к серверу: {url} имеет ошибку {error}. '
              'Параметры: {params}')
CODE_ERROR = ('Попытка обращения к серверу: {url}, параметры: {params}. '
              'В результате присутствует {code}. Ошибка {error}.')
STATUS = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
}
STATUS_ERROR = 'Получен не ожидаемый статус работы: {status}'
ANSWER = 'У вас проверили работу "{homework_name}" от {date}!\n\n{verdict}'
BOT_ERROR = 'Бот столкнулся с ошибкой: {e}'


def parse_homework_status(homework):
    name = homework['homework_name']
    status = homework['status']
    date = homework['date_updated']
    if status not in STATUS.keys():
        raise ValueError(STATUS_ERROR.format(status=status))
    verdict = STATUS[status]
    return ANSWER.format(homework_name=name,
                         verdict=verdict,
                         date=date)


def get_homework_statuses(current_timestamp):
    params = {
        'from_date': current_timestamp
    }
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.HTTPError(REQUEST_ERROR.format(
            url=URL,
            params=params,
            headers=HEADERS,
            e=e
        ))
    res = response.json()
    if 'error' in res:
        error = res['error']['error']
        raise ValueError(BAD_STATUS.format(
            url=URL,
            error=error,
            params=params
        ))
    if 'code' in res:
        code = res['code']
        error = res['message']
        raise ValueError(CODE_ERROR.format(
            url=URL,
            params=params,
            code=code,
            error=error
        ))
    return res


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
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            logging.error(BOT_ERROR.format(e=e))
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(
        filename=__file__ + '.log',
        format='%(asctime)s %(funcName)s %(message)s'
    )
    main()
