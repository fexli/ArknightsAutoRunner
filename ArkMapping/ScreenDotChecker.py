from typing import Tuple

from .ScreenDotSaver import ScreenDotSaver
import numpy as np


class ScreenDotChecker(object):
    def __init__(self, ark=None, configPath=".\\ArkMapping\\MapData.dat"):
        self.saver = ScreenDotSaver(arkRunner=ark, path=configPath)

    def getDistance(self, d1, d2):
        return np.linalg.norm(np.array(d1) - np.array(d2)) / 441.6729559300637

    def save(self):
        return self.saver.writeData()

    def addMap(self, name):
        return self.saver.createMap(name)

    def delMap(self, name):
        return self.saver.removeMap(name)

    def check(self, image, where="AUTO"):
        if where == "AUTO":
            score_list = {}
            for name in self.saver.config:
                score = []
                for x, y, r, g, b in self.saver.config.get(name):
                    score.append(self.getDistance((b, g, r), image[y - 1][x - 1]))
                score_list.update({name: score})
            return score_list
        else:
            if self.saver.config.get(where) is None:
                return None
            score = []
            for x, y, r, g, b in self.saver.config.get(where):
                score.append(self.getDistance((b, g, r), image[y - 1][x - 1]))
            return score

    def addPoint(self, name, image, x, y):
        return self.saver.addPoint(name, x, y, image)

    def addPoints(self, name, image, *pos: Tuple[Tuple[int, int]]) -> bool:
        for x, y in pos:
            self.addPoint(name, image, x, y)
        return True
