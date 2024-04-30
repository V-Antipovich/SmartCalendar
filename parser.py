from bs4 import BeautifulSoup
import requests
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import sqlite3 as sql
from config import spreadsheet_id

def parse():
    today = datetime.datetime.now().strftime("%d.%m.%Y").split('.')
    months = dict([('January', 1), ('February', 2), ('March', 3), ('April', 4), ('May', 5), ('June', 6), ('July', 7), ('August', 8), ('September', 9), ('October', 10), ('November', 11), ('December', 12)])
    pageNumber = 1
    new_rows = []

    while pageNumber < 20:
        url = 'https://events.educom.ru/calendar?onlyActual=true&pageNumber=' + str(pageNumber) + '&search='
        source_code = requests.get(url)
        plain_text = source_code.text
        soup = BeautifulSoup(plain_text, 'html.parser')
        results = soup.findAll('section', {'class': ['event-card small-12 grid-x']})
        for result in results:
            if result.find('div', {'class': ['event-card__content-status small-12 grid-x align-middle error']}):
                continue
            soup_event = result.find('a')
            event = soup_event.text.strip()
            soup_start_time = result.find('div', {'class': ['event-card__date-time small-2 grid-y align-center-middle']})
            current_start_time = soup_start_time.text.strip()[:-4]
            soup_date = result.find('p')
            date_uncut = soup_date.text.replace('\n', '').strip()
            f_space, e_space = date_uncut.find(' '), date_uncut.rfind(' ')
            date_day = date_uncut[:f_space]
            date_month = months[date_uncut[e_space+1:]]
            date_year = 0
            if date_month < int(today[1]):
                date_year = today[2]+'1'
            else:
                date_year = today[2]
            date = str(date_day) + '.' +  str(date_month) + '.' + str(date_year)

            soup_place = result.find('div', {'class': ['event-card__content-description-address']})
            if soup_place:
                place = soup_place.text
            else:
                place = 'Дистанционно'
            duration = result.find('span', {'class': ["event-card__content-image-stat-clock"]}).text

            #new_row = []

            now = str(datetime.datetime.now())
            now = now.replace('-', '.')
            now = now.replace(' ', '.')
            now = now.replace(':', '.')
            id = sum([int(i) for i in now.split('.')])
            """
            new_row.append(id)
            new_row.append(event)
            new_row.append(date)
            new_row.append(current_start_time)
            new_row.append(duration)
            new_row.append(place)
            """
            new_row = (event, date, current_start_time, duration, place)
            new_rows.append(new_row)

        pageNumber += 1
    print(len(new_rows))
    new_rows = list(set(new_rows))
    print(len(new_rows))

    # Авторизация
    CREDENTIALS_FILE = 'creds.json'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive'])
    httpAuth = credentials.authorize(httplib2.Http())
    service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

    # Проверяем наличие понравившихся, добавляем в список событий
    old_values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='A2:E1000',
        majorDimension='ROWS'
    ).execute()

    # Убираем из новых событий те, что есть среди старых
    try:
        old_values = old_values["values"]
        for value in old_values:
            if new_rows.count(value) > 1:
                new_rows.remove(value)
        len_old_values = len(old_values)
    except KeyError:
        len_old_values = 0

    extra_rows = []
    for i in range(len(new_rows)):
        extra_row = []
        extra_row.append('Не определился')
        extra_row.append(True)
        extra_rows.append(extra_row)

    #  Записываем инфу в таблицу
    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": "A" + str(2 + len_old_values) + ":E" + str(len(new_rows) + len_old_values + 1),
                 "majorDimension": "ROWS",
                 "values": new_rows},
                {"range": "F" + str(2 + len_old_values) + ":G" + str(len(new_rows) + len_old_values + 1),
                 "majorDimension": "ROWS",
                 "values": extra_rows}
            ]
        }
    ).execute()
    """
        # А теперь загружаем в базу

    conn = sql.connect('Events.db')
    cur = conn.cursor()

    cur.execute(" CREATE TABLE IF NOT EXISTS new_events(
    ID INT NOT NULL,
    summary TEXT,
    date TEXT,
    start_time TEXT,
    duration TEXT,
    place TEXT,
    isnew TEXT,
    UNIQUE(summary, date, start_time, duration)
    );")
    conn.commit()

    cur.executemany(
    "INSERT OR IGNORE INTO new_events VALUES(?, ?, ?, ?, ?, ?, ?);", new_rows)
    conn.commit()

    conn.close()
    return True
"""
if __name__ == '__main__':
    parse()
