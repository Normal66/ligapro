import requests
from bs4 import BeautifulSoup
import re
from datetime import *
from dateutil.relativedelta import *
import calendar
from dateutil.rrule import *
from dateutil.parser import *
from datetime import *

PERIOD = 3        # За сколько месяцев брать матчи
TOURS_URL = 'https://tt.sport-liga.pro/tours/'


def make_list_url_by_day() -> list:
    # Формируем список url по дням за период с TODAY-PERIOD по TODAY ввиде:
    # https://tt.sport-liga.pro/tours/?year=2021&month=11&day=4
    _result = []
    _tmp = list(list(rrule(DAILY, dtstart=date.today()+relativedelta(months=-PERIOD), until=date.today())))
    for _items in _tmp:
        _result.append(f'{TOURS_URL}?year={_items.year}&month={_items.month}&day={_items.day}')
    return _result


if __name__ == '__main__':
    print(make_list_url_by_day())
