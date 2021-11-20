# Подготавливает список матчей в файл allgame.json
import requests
from bs4 import BeautifulSoup
import re
from dateutil.relativedelta import *
from dateutil.rrule import *
from datetime import *
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import json

TEST_TOUR_URL = 'https://tt.sport-liga.pro/tours/13241'
PERIOD = 2        # За сколько месяцев брать матчи
TOURS_URL = 'https://tt.sport-liga.pro/tours/'
get_href = re.compile(r'href=\"([^\"]*)\"')


def get_date(inp_date: str) -> date:
    _month = None
    _day, _tmp_month, _year = inp_date.split(' ')
    if 'Янв' in _tmp_month:
        _month = 1
    if 'Фев' in _tmp_month:
        _month = 2
    if 'Мар' in _tmp_month:
        _month = 3
    if 'Апр' in _tmp_month:
        _month = 4
    if 'Май' in _tmp_month:
        _month = 5
    if 'юн' in _tmp_month:
        _month = 6
    if 'юл' in _tmp_month:
        _month = 7
    if 'Авг' in _tmp_month:
        _month = 8
    if 'Сен' in _tmp_month:
        _month = 9
    if 'Окт' in _tmp_month:
        _month = 10
    if 'Ноя' in _tmp_month:
        _month = 11
    if 'Дек' in _tmp_month:
        _month = 12
    return datetime(int(_year.strip()), _month, int(_day.strip()))


def get_list_url_tours(inp_url: str) -> list:
    # Формируем список url прошедших турниров
    _result = []
    r = requests.get(inp_url)
    src = BeautifulSoup(r.text, 'html.parser')
    tmp_url = src.findAll('td', {'class': 'tournament-name'})
    list_url = get_href.findall(str(tmp_url))
    for _item in list_url:
        _result.append('https://tt.sport-liga.pro/' + _item)
    return _result


def make_list_url_by_day() -> list:
    # Формируем список url по дням за период с TODAY-PERIOD по TODAY ввиде:
    # https://tt.sport-liga.pro/tours/?year=2021&month=11&day=4
    _result = []
    _tmp = list(list(rrule(DAILY, dtstart=date.today()+relativedelta(months=-PERIOD), until=date.today())))
    for _items in _tmp:
        _result.append(f'{TOURS_URL}?year={_items.year}&month={_items.month}&day={_items.day}')
    return _result


def initial_data_filling(list_url: list, out_files='tennis.json') -> list:
    _res = []
    _i = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for url in list_url:
            futures.append(executor.submit(get_list_url_tours, inp_url=url))
        for future in concurrent.futures.as_completed(futures):
            _res.append(future.result())
            _i += 1
            print(_i, ' из ', len(list_url), end='\r')
    _res = [x for x in _res if x]
    data = []
    for _item in _res:
        for _items in _item:
            data.append(_items)
#    with open(out_files, 'w', encoding='utf-8') as f:
#        json.dump(data, f, ensure_ascii=False, indent=4)
    return data


def get_list_match_by_tour(inp_url: str):
    # Возвращает словарь статистики игр в турнире
    _result = []
    r = requests.get(inp_url)
    src = BeautifulSoup(r.text, 'html.parser')
    _date = src.title.text.split('-')[0].strip()
    _table = src.find('table', {'class': 'games_list'})
    _tr = _table.find_all('tr')
    for row in _tr:
        _col = row.find_all('td')
        _tmp = BeautifulSoup(str(_col), 'html.parser')
        try:
            _a = _tmp.find_all('td', {'class': 'right'})
            _c = _tmp.find_all('td', {'class': 'score'})
            _d = _tmp.find_all('td', {'class': 'left'})
            _b = _tmp.find_all('td', {'class': 'rating'})
            if _a and _b and _c and _d:
                _tmp_res = {}
                # Дата игры
                _tmp_res['date'] = get_date(_date)
                # Время игры
                # Игрок 1
                _tmp = re.findall(r'([-а-яА-Я]+)', str(_a))
                _tmp_res['player1'] = f"{_tmp[0]} {_tmp[1]}"
                # Игрок 2
                _tmp = re.findall(r'([-а-яА-Я]+)', str(_d))
                _tmp_res['player2'] = f"{_tmp[0]} {_tmp[1]}"
                _tmp = re.findall(r'\d{3}', str(_b))
                # Рейтинг Игрока 1
                _tmp_res['rating1'] = int(_tmp[0])
                # Рейтинг Игрока 2
                _tmp_res['rating2'] = int(_tmp[1])
                # Diif рейтинга
                _tmp_res['diff'] = abs(_tmp_res['rating1'] - _tmp_res['rating2'])
                # Счёт
                _tmp = re.findall(r'\d : \d', str(_c))[0]
                _score1, _score2 = _tmp.split(':')
                _tmp_res['score1'] = int(_score1.strip())
                _tmp_res['score2'] = int(_score2.strip())
                # Сеты
                _tmp_res['sets'] = re.findall(r'(\d+-\d+)+', str(_c))
                _result.append(_tmp_res)
        except:
            pass
    return _result


def make_full(list_url):
    _res = []
    _i = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for url in list_url:
            futures.append(executor.submit(get_list_match_by_tour, inp_url=url))
        for future in concurrent.futures.as_completed(futures):
            _res.append(future.result())
            _i += 1
            print(_i, ' из ', len(list_url), end='\r')
    _res = [x for x in _res if x]
    data = []
    for _item in _res:
        for _items in _item:
            data.append(_items)
    with open('allgame.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=True, default=str)
    return data


def prepare_game():
    _ = make_full(initial_data_filling(make_list_url_by_day()))


if __name__ == '__main__':
    prepare_game()
