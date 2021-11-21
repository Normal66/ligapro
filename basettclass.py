# Базовый класс сбора статистики
import pandas as pd
import config
import json
import requests
from bs4 import BeautifulSoup
import re
get_href = re.compile(r'href=\"([^\"]*)\"')


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
                _rating = int(_table.find('h2').text)
    return _rating


class TableTennis(object):
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
                if _i == 2:
                    self._src.loc[_ind, 'Set2'] = _set_total
                if _i == 3:
                    self._src.loc[_ind, 'Set3'] = _set_total
                if _i == 4:
                    self._src.loc[_ind, 'Set4'] = _set_total
                if _i == 5:
                    self._src.loc[_ind, 'Set5'] = _set_total
                _i += 1
            self._src.loc[_ind, 'Total'] = _total
        self._src.drop('sets', axis=1, inplace=True)

    def update(self) -> None:
        pass

    def game_30(self):
        _df = self._src.loc[((self._src['score1'] == 3) & (self._src['score2'] == 0)) |
                            ((self._src['score1'] == 0) & (self._src['score2'] == 3))]
        return _df

    def test_two_player(self, pl1, pl2):
        _df = self._src.loc[((self._src['player1'] == pl1) & (self._src['player2'] == pl2)) |
                            ((self._src['player1'] == pl2) & (self._src['player2'] == pl1))]
        if len(_df) == 0:
            return None
        _df.loc[:, "Set1"] = int(0)
        _df.loc[:, "Set2"] = int(0)
        _df.loc[:, "Set3"] = int(0)
        _df.loc[:, "Set4"] = int(0)
        _df.loc[:, "Set5"] = int(0)
        _df.loc[:, "Total"] = int(0)
        # Рассчитываем тоталы по сетам и тотал по матчу
        for _ind, item in _df.iterrows():
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
                    _df.loc[_ind, 'Set1'] = _set_total
                if _i == 2:
                    _df.loc[_ind, 'Set2'] = _set_total
                if _i == 3:
                    _df.loc[_ind, 'Set3'] = _set_total
                if _i == 4:
                    _df.loc[_ind, 'Set4'] = _set_total
                if _i == 5:
                    _df.loc[_ind, 'Set5'] = _set_total
                _i += 1
            _df.loc[_ind, 'Total'] = _total
        _df.drop('sets', axis=1, inplace=True)
#        print(_df.to_string(index=False))
        print(_df)
        return _df
