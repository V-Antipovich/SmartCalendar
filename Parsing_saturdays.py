from bs4 import BeautifulSoup
import requests
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from config import spreadsheet_id, CREDENTIALS_FILE


today = datetime.datetime.now().strftime("%d.%m.%Y").split('.')
months = dict([('January', 1), ('February', 2), ('March', 3), ('April', 4), ('May', 5), ('June', 6), ('July', 7), ('August', 8), ('September', 9), ('October', 10), ('November', 11), ('December', 12)])
pageNumber = 1
events, places, start_time, durations, dates, interested_in, new_rows = [], [], [], [], [], [], []

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
        events.append(event)
        soup_start_time = result.find('div', {'class': ['event-card__date-time small-2 grid-y align-center-middle']})

        start_time.append(soup_start_time.text.strip()[:-4])
        current_start_time = start_time[-1]
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
        dates.append(date)

        soup_place = result.find('div', {'class': ['event-card__content-description-address']})
        place = soup_place.text
        places.append(place)

        duration = result.find('span', {'class': ['event-card__content-image-stat-clock']}).text
        durations.append(duration[1:])

        new_row = []
        new_row.append(event)
        new_row.append(date)
        new_row.append(start_time[-1])
        new_row.append(duration[1:])
        new_row.append(place)
        new_rows.append(new_row)
    pageNumber += 1
# Авторизация

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)

# Проверяем наличие понравившихся, добавляем в список событий
old_values = service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range='A2:E1000',
    majorDimension='ROWS'
).execute()

#Убираем из новых событий повторяющиеся
for i in range(7):
    for row in new_rows:
        if new_rows.count(row) > 1:
            new_rows.remove(row)

# Убираем из новых событий те, что есть среди старых
try:
    old_values = old_values["values"]
    for value in old_values:
        if new_rows.count(value)>1:
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
        {"range": "A"+str(2 + len_old_values)+":E"+str(len(new_rows) + len_old_values + 1),
        "majorDimension": "ROWS",
        "values": new_rows},
        {"range": "F" + str(2 + len_old_values) + ":G"+str(len(new_rows) + len_old_values + 1),
        "majorDimension": "ROWS",
         "values": extra_rows}
        ]
        }
    ).execute()
