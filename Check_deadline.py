import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials
from config import spreadsheet_id
import datetime

today = [int(i) for i in datetime.datetime.now().strftime("%d-%m-%Y").split('-')]

CREDENTIALS_FILE = 'creds.json'

# Авторизация
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

values = service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range='B2:B1000000',
    majorDimension='COLUMNS'
).execute()
dates = values['values'][0]
if_deadline = []
for date in dates:
    date = [int(i) for i in date.split('.')]
    if_deadline.append(today[0] + 1 == date[0] and today[1] == date[1] and today[2] == today[2])
values = service.spreadsheets().values().batchUpdate(
spreadsheetId=spreadsheet_id,
body={
    "valueInputOption": "USER_ENTERED",
    "data": [
        {"range": "H2:H"+str(len(dates)+1),
         "majorDimension": "COLUMNS",
         "values": [if_deadline]}
        ]
        }
    ).execute()

