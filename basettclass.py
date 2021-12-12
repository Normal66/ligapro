# Базовый класс сбора статистики
import datetime
from prepare import prepare_game
import pandas as pd
import config
import json
import requests
from bs4 import BeautifulSoup
import re
from dateutil.relativedelta import *
from dateutil.rrule import *
from datetime import *
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List

get_href = re.compile(r'href=\"([^\"]*)\"')
TOURS_URL = 'https://tt.sport-liga.pro/tours/'

def get_curr_rating(player: str) -> int:
    # Возвращает текущий рейтинг игрока
    _rating = 0
    url = config.url_start_page_player.get(player[0])
    gcr_r = requests.get(url)
    src = BeautifulSoup(gcr_r.text, 'html.parser')
    _table = src.find('table', {'class': 'bordered-table'})
    _tr = _table.find_all('tr')
    for row in _tr:
        _col = row.find_all('a')
        for _items in _col:
            if str(_items).find(player) > 0:
                id_player = get_href.findall(str(_items))[0]
                # Запрашиваем страницу пользователя
                url_player = f"https://tt.sport-liga.pro/{id_player}"
                gcr_r = requests.get(url_player)
                src = BeautifulSoup(gcr_r.text, 'html.parser')
                _table = src.find('table', {'class': 'user-rating-table'})
                try:
                    _rating = int(_table.find('h2').text)
                except AttributeError:
                    _rating = 0
    return _rating


# Возвращает True, если входящее время "00:00" лежит в диапазоне текущий_час
def time_in_hour(inp_time):
    import datetime
    current_hour = datetime.datetime.now().time().hour - 2
    check_hour, check_minute = inp_time.split(':')
    check_hour = int(check_hour)  # Нам нужно местное время, а там - московское!
    if (check_hour >= current_hour) and (check_hour < current_hour + 1):
        return True
    else:
        return False


def make_prognoz_next_hour() -> list:
    _current_prognoz = []
    # Только со статусом "не начался".
    r = requests.get('https://tt.sport-liga.pro/#pills-today')
    r.encoding = 'utf-8'
    src = BeautifulSoup(r.text, 'html.parser')
    _up = src.find('div', {'id': 'pills-today'})
    _index_games = _up.find('div', {'class': 'index_games'})
    _list_game = _index_games.findAll('div', {'class': 'tour-link'})
    _today = []
    for item in _list_game:
        _local_res = {}
        _links = item.findAll('a')
        _local_res['status'] = _links[1].text
        _local_res['time'] = _links[0].text
        _local_res['player1'] = _links[2].text
        _local_res['score'] = _links[3].text
        _local_res['player2'] = _links[4].text
        _today.append(_local_res)
    for _items in _today:
        if (_items['status'] == 'не начался') and (time_in_hour(_items['time'])):
            # TODO Проверяем, а нет ли такого прогноза
            _tmp = {}
            _tmp['player1'] = _items['player1']
            _tmp['player2'] = _items['player2']
            _tmp['time'] = _items['time']
            _current_prognoz.append(_tmp)
    return _current_prognoz


@dataclass_json
@dataclass(frozen=True)
class Sets:
    SetP1: int
    SetP2: int


@dataclass_json
@dataclass
class TTRecord:
    P1: str = ''
    R1: int = 0
    P2: str = ''
    R2: int = 0
    DG: str = ''
    SC: str = ''
    ST: List[Sets] = None


class TTMinimal(object):
    def __init__(self):
        super(TTMinimal, self).__init__()
        self._ystd = self.yesterday()
        self._tiday = self.today()

    def yesterday(self) -> List:
        _list_game = []
        yesterday = str(date.today() - timedelta(days=1))
        r = requests.get('https://tt.sport-liga.pro/#pills-yesterday')
        r.encoding = 'utf-8'

        src = BeautifulSoup(r.text, 'html.parser')
        _root = src.find_all('div', {'class': 'tour-link'})
        for _items in _root:
            _rec = TTRecord()
            _tmp = _items.find_all('a', {'class': 'text-white'})
            _rec.DG = yesterday
            _rec.P1 = _tmp[0].text.strip()
            _rec.P2 = _tmp[1].text.strip()
            _tmp = _items.find_all('span', {'class': 'text-info'})
            _rec.R1 = _tmp[0].text.strip()
            _rec.R2 = _tmp[1].text.strip()
            _rec.SC = _items.find('a', {'class': 'text-info'}).text
            _tmp = _items.find_all('span', {'class': 'text-white'})
            _sets_tmp = []
            for _item in _tmp:
                _s1, _s2 = _item.text.split('-')
                _sets = Sets(int(_s1), int(_s2))
                _sets_tmp.append(_sets)
            _rec.ST = _sets_tmp
            _list_game.append(_rec)
        return _list_game

    def today(self) -> List:
        r = requests.get('https://tt.sport-liga.pro/#pills-today')
        _list_game = []
        today = str(date.today())
        r.encoding = 'utf-8'

        src = BeautifulSoup(r.text, 'html.parser')
        _root = src.find_all('div', {'class': 'tour-link'})
        for _items in _root:
            _rec = TTRecord()
            _tmp = _items.find_all('a', {'class': 'text-white'})
            _rec.DG = today
            _rec.P1 = _tmp[0].text.strip()
            _rec.P2 = _tmp[1].text.strip()
            _tmp = _items.find_all('span', {'class': 'text-info'})
            _rec.R1 = _tmp[0].text.strip()
            _rec.R2 = _tmp[1].text.strip()
            _rec.SC = _items.find('a', {'class': 'text-info'}).text
            _tmp = _items.find_all('span', {'class': 'text-white'})
            _sets_tmp = []
            for _item in _tmp:
                _s1, _s2 = _item.text.split('-')
                _sets = Sets(int(_s1), int(_s2))
                _sets_tmp.append(_sets)
            _rec.ST = _sets_tmp
            _list_game.append(_rec)
        return _list_game


class TableTennis(object):
    # TODO Добавить результаты последних N игр соперников с другими игроками. Например: P1, P2
    # n игр P1 vs Pm, P2 vs Pm в формате
    #       Pm  Pm  Pm
    # P1    1:3 0:3 2:3
    # P2    3:2 3:2 1:3
    def __init__(self):
        super(TableTennis, self).__init__()
        with open('allgame.json', 'r', encoding='utf-8') as fp:
            _l_data = json.load(fp)
        self._src = pd.json_normalize(_l_data)
        self._src = self._src.sort_values(by='date')
        self._src.loc[:, "Set1"] = int(0)
        self._src.loc[:, "Set2"] = int(0)
        self._src.loc[:, "Set3"] = int(0)
        self._src.loc[:, "Set4"] = int(0)
        self._src.loc[:, "Set5"] = int(0)
        self._src.loc[:, "Total"] = int(0)

        self._src.loc[:, "Set1P1"] = int(0)
        self._src.loc[:, "Set1P2"] = int(0)
        self._src.loc[:, "Set2P1"] = int(0)
        self._src.loc[:, "Set2P2"] = int(0)
        self._src.loc[:, "Set3P1"] = int(0)
        self._src.loc[:, "Set3P2"] = int(0)
        self._src.loc[:, "Set4P1"] = int(0)
        self._src.loc[:, "Set4P2"] = int(0)
        self._src.loc[:, "Set5P1"] = int(0)
        self._src.loc[:, "Set5P2"] = int(0)

        # Рассчитываем тоталы по сетам и тотал по матчу
        for _ind, item in self._src.iterrows():
            _tmp_set = item['sets']
            # Обрабатываем набор и считаем тотал
            _total = 0
            _i = 1
            for _items in _tmp_set:
                _set_total = 0
                _a, _b = _items.split('-')
                _set_total = int(_a) + int(_b)
                _total += int(_a) + int(_b)
                if _i == 1:
                    self._src.loc[_ind, 'Set1'] = _set_total
                    self._src.loc[_ind, 'Set1P1'] = int(_a)
                    self._src.loc[_ind, 'Set1P2'] = int(_b)
                if _i == 2:
                    self._src.loc[_ind, 'Set2'] = _set_total
                    self._src.loc[_ind, 'Set2P1'] = int(_a)
                    self._src.loc[_ind, 'Set2P2'] = int(_b)

                if _i == 3:
                    self._src.loc[_ind, 'Set3'] = _set_total
                    self._src.loc[_ind, 'Set3P1'] = int(_a)
                    self._src.loc[_ind, 'Set3P2'] = int(_b)

                if _i == 4:
                    self._src.loc[_ind, 'Set4'] = _set_total
                    self._src.loc[_ind, 'Set4P1'] = int(_a)
                    self._src.loc[_ind, 'Set4P2'] = int(_b)

                if _i == 5:
                    self._src.loc[_ind, 'Set5'] = _set_total
                    self._src.loc[_ind, 'Set5P1'] = int(_a)
                    self._src.loc[_ind, 'Set5P2'] = int(_b)

                _i += 1
            self._src.loc[_ind, 'Total'] = _total
#        self._src.drop('sets', axis=1, inplace=True)

    def get_src(self):
        return self._src

    def update(self) -> None:
        """
        0) Получаем дату последней игры в списке ( LastData )
        1) Удаляем игры за LastData
        2) Добавляем игры за период = LastData - Сегодня]
        """
        prepare_game()
        _res = []
        _t = self._src.tail(1)
        LastDate = _t['date'].iloc[0]
        self._src = self._src.loc[self._src['date'] != LastDate]
        # Добавляем данные из update.json
        with open('update.json', 'r', encoding='utf-8') as fp:
            _l_data = json.load(fp)
        _upd = pd.json_normalize(_l_data)
        self._src = pd.concat([self._src, _upd], ignore_index=True)
        self._src = self._src.sort_values(by='date')

    def yesterday(self):
        yesterday = date.today() - timedelta(days=1)
        r = requests.get('https://tt.sport-liga.pro/#pills-yesterday')
        src = BeautifulSoup(r.text, 'html.parser')
        _root = src.find_all('div', {'class': 'tour-link'})
        for _items in _root:
            _rec = TTRecord()
            _tmp = _items.find_all('a', {'class': 'text-white'})
            _rec.DG = yesterday
            _rec.P1 = _tmp[0].text.strip()
            _rec.P2 = _tmp[1].text.strip()
            _tmp = _items.find_all('span', {'class': 'text-info'})
            _rec.R1 = _tmp[0].text.strip()
            _rec.R2 = _tmp[1].text.strip()
            _rec.SC = _items.find('a', {'class': 'text-info'}).text
            _tmp = _items.find_all('span', {'class': 'text-white'})
            _sets = []
            for _item in _tmp:
                _sets.append(_item.text)
            _rec.ST = _sets
            print('\n--------------\n', _rec)
        pass

    def today(self):
        r = requests.get('https://tt.sport-liga.pro/#pills-today')
        src = BeautifulSoup(r.text, 'html.parser')
        _root = src.find_all('div', {'class': 'tour-link'})
        for _items in _root:
            #            print('\n--------------\n', _items)
            _tmp = _items.find_all('a', {'class': 'text-white'})
            player1 = _tmp[0].text.strip()
            player2 = _tmp[1].text.strip()
            _tmp = _items.find_all('span', {'class': 'text-info'})
            player1_rating = _tmp[0].text.strip()
            player2_rating = _tmp[1].text.strip()
            _score = _items.find('a', {'class': 'text-info'})
            _tmp = _items.find_all('span', {'class': 'text-white'})
            _sets = []
            for _item in _tmp:
                _sets.append(_item.text)
            print(_sets)
            print(f"P1 {player1} R1 {player1_rating}\tP2 {player2} R2 {player2_rating}")
            print('\n--------------\n')
        pass

    def game_20(self, inp_clear=False):
        # Возвращает игры со счётом 2:0 или 0:2
        _df = self._src.loc[
            ((self._src['Set1P1'] > self._src['Set1P2']) & (self._src['Set2P1'] > self._src['Set2P2']))
            |
            ((self._src['Set1P1'] < self._src['Set1P2']) & (self._src['Set2P1'] < self._src['Set2P2']))
        ]
        if inp_clear:   # Очистка нужна
            _df.drop(['date', 'rating1', 'rating2', 'score1', 'score2', 'Set1P1', 'Set1P2', 'Set2P1', 'Set2P2',
                            'Set3P1', 'Set3P2', 'Set4P1', 'Set4P2', 'Set5P1', 'Set5P2'], axis=1, inplace=True)
        return _df

    def game_30(self):
        _df = self._src.loc[((self._src['score1'] == 3) & (self._src['score2'] == 0)) |
                            ((self._src['score1'] == 0) & (self._src['score2'] == 3))]
        return _df

    def game_11(self, inp_clear=False):
        # Возвращает игры со счётом 1:1
        _df = self._src.loc[
            ((self._src['Set1P1'] > self._src['Set1P2']) & (self._src['Set2P1'] < self._src['Set2P2']))
            |
            ((self._src['Set1P1'] < self._src['Set1P2']) & (self._src['Set2P1'] > self._src['Set2P2']))
            ]
        if inp_clear:  # Очистка нужна
            _df.drop(['date', 'rating1', 'rating2', 'score1', 'score2', 'Set1P1', 'Set1P2', 'Set2P1', 'Set2P2',
                      'Set3P1', 'Set3P2', 'Set4P1', 'Set4P2', 'Set5P1', 'Set5P2'], axis=1, inplace=True)
        return _df

    def game_31(self):
        # Возвращает игры со счётом 3:1 или 1:3
        _df = self._src.loc[((self._src['score1'] == 3) & (self._src['score2'] == 1)) |
                            ((self._src['score1'] == 1) & (self._src['score2'] == 3))]
        return _df

    def game_32(self):
        # Возвращает игры со счётом 3:2 или 2:3
        _df = self._src.loc[((self._src['score1'] == 3) & (self._src['score2'] == 2)) |
                            ((self._src['score1'] == 2) & (self._src['score2'] == 3))]
        return _df

    def test_two_player(self, pl1, pl2):
        _df = self._src.loc[((self._src['player1'] == pl1) & (self._src['player2'] == pl2)) |
                            ((self._src['player1'] == pl2) & (self._src['player2'] == pl1))].tail()
        # Вот тут нам бы еще и текущие рейтинги не помешали бы...
        r1 = get_curr_rating(pl1)
        r2 = get_curr_rating(pl2)
        return _df, [r1, r2]


class TTPlayer(TableTennis):
    # Класс одного игрока
    def __init__(self, _player):
        super().__init__()
        # dataframe по игроку
        self.oneplayer = self._src.loc[(self._src['player1'] == _player) | (self._src['player2'] == _player)]
        self.oneplayer = self.oneplayer.sort_values(by='date')
        self.oneplayer = self.oneplayer.astype({'score1': 'Int64', 'score2': 'Int64'})
        self.oneplayer.drop(['diff', 'rating1', 'rating2', 'Set1P1', 'Set1P2', 'Set2P1', 'Set2P2', 'Set3P1', 'Set3P2', 'Set4P1', 'Set4P2', 'Set5P1', 'Set5P2'], axis=1, inplace=True)
        self.player = _player
        self.rating = get_curr_rating(self.player)

    def test_two_pl(self, sopernik):
        _df = self.oneplayer.loc[
            (self.oneplayer['player1'] == sopernik) | (self.oneplayer['player2'] == sopernik)
        ].tail()
        # Вот тут нам бы еще и текущие рейтинги не помешали бы...
        r2 = get_curr_rating(sopernik)
        return _df, [self.rating, r2]

    def make_list_opponent(self):
        # Создает список соперников, с которыми встречались
        _out_list = []
        _l1 = self.oneplayer['player1'].tolist()
        _l1.remove(self.player)
        _l2 = self.oneplayer['player2'].tolist()
        _l2.remove(self.player)
        _out_list = list(set(_l1 + _l2))
        return _out_list


class TTPlayers(TableTennis):
    # Класс двух игроков
    def __init__(self, _player1, _player2):
        super().__init__()
        self.player1 = _player1
        self.player2 = _player2
        # Все игры первого игрока
        self.game_pl1 = self._src.loc[(self._src['player1'] == _player1) | (self._src['player2'] == _player1)]
        # Все игры второго игрока
        self.game_pl2 = self._src.loc[(self._src['player1'] == _player2) | (self._src['player2'] == _player2)]
        # Все игры между собой
        self.game_bw = self._src.loc[
            ((self._src['player1'] == _player1) & (self._src['player2'] == _player2)) |
            ((self._src['player1'] == _player2) & (self._src['player2'] == _player1))
            ].tail()
        self.game_bw.drop(
            ['diff', 'rating1', 'rating2', 'Set1P1', 'Set1P2', 'Set2P1', 'Set2P2', 'Set3P1', 'Set3P2', 'Set4P1',
             'Set4P2', 'Set5P1', 'Set5P2'], axis=1, inplace=True)

    def game_between_each_other(self):
        # Игры между собой
        return self.game_bw

    def game_with_other(self):
        # Игры с одним и тем же соперником у обоих
        # Создаем список оппонентов, с которыми играли оба игрока
        _res = []
        _tmp1 = self.game_pl1['player1'].tolist()
        _tmp2 = self.game_pl1['player2'].tolist()
        list_pl1 = list(set(_tmp1 + _tmp2))         # Список оппонентов первого игрока
        _tmp1 = self.game_pl2['player1'].tolist()
        _tmp2 = self.game_pl2['player2'].tolist()
        list_pl2 = list(set(_tmp1 + _tmp2))         # Список оппонентов второго игрока
        # Сравниваем списки между собой и формируем выходной список оппонентов
        result = list(set(list_pl1) & set(list_pl2))
        result.remove(self.player1)
        result.remove(self.player2)
        # Формируем результаты встреч
        for _opponent in result:
            # Для первого игрока
            _tmp_first = self.game_pl1.loc[(self.game_pl1['player1'] == _opponent) | (self.game_pl1['player2'] == _opponent)].tail()
            _tmp_first.drop(
                ['diff', 'rating1', 'rating2', 'Set1P1', 'Set1P2', 'Set2P1', 'Set2P2', 'Set3P1', 'Set3P2', 'Set4P1',
                 'Set4P2', 'Set5P1', 'Set5P2'], axis=1, inplace=True)
            # Для второго игрока
            _tmp_second = self.game_pl2.loc[(self.game_pl2['player1'] == _opponent) | (self.game_pl2['player2'] == _opponent)].tail()
            _tmp_second.drop(
                ['diff', 'rating1', 'rating2', 'Set1P1', 'Set1P2', 'Set2P1', 'Set2P2', 'Set3P1', 'Set3P2', 'Set4P1',
                 'Set4P2', 'Set5P1', 'Set5P2'], axis=1, inplace=True)

            # Меньше 3 игр не рассматриваем!!!
            if (len(_tmp_first) > 3) and (len(_tmp_second) > 3):
                _res.append([_tmp_first, _tmp_second])
        return _res
