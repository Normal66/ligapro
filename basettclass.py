# Базовый класс сбора статистики
from prepare import prepare_game
import pandas as pd
import numpy as np
import json


class TableTennis(object):
    def __init__(self):
        super(TableTennis, self).__init__()
        with open('allgame.json', 'r', encoding='utf-8') as fp:
            _l_data = json.load(fp)
        self._src = pd.json_normalize(_l_data)
        self._src = self._src.sort_values(by='date')

    def game_30(self):
        print(self._src)
        print(self._src.info())
        _df = self._src.loc[((self._src['score1'] == 3) & (self._src['score2'] == 0)) |
                            ((self._src['score1'] == 0) & (self._src['score2'] == 3))]
        return _df
