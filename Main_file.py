from bs4 import BeautifulSoup
import requests
import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials
from random import choice
from string import ascii_letters
import os

# Парсинг Events.educom.ru, занесение в таблицу данных о событии, месте проведения,
os.system('Parsing_saturdays.py')
# Проверка наличия событий, которые произойдут завтра
os.system('Check_deadline.py')

import Parsing_saturdays
import Check_deadline