from utils.logger import root_logger as logger
import time
import json
import os


class ScreenDotSaver(object):
    def __init__(self, arkRunner=None, path=".\\ArkMapping\\MapData.dat"):
        self.ark = arkRunner
        self.savePath = path
        self.config = dict()
        if os.path.exists(path):
            self.readData()

    def readData(self):
        with open(self.savePath, "r")as f:
            self.config = json.load(f)

    def writeData(self):
        with open(self.savePath, "w") as f:
            json.dump(self.config, f, ensure_ascii=False)

    def createMap(self, name):
        if self.config.get(name) is None:
            self.config.update({name: []})
            return True
        else:
            logger.warning("已存在名为%s的数据" % name)
            return False

    def removeMap(self, name):
        if self.config.get(name) is None:
            logger.error("不存在名为%s的数据" % name)
        self.config.pop(name)

    def addPoint(self, name, x, y, image) -> bool:
        if self.config.get(name) is None:
            self.config.update({name: []})

        b, g, r = image[y - 1][x - 1]
        self.config.get(name).append([x, y, int(r), int(g), int(b)])
        return True

    def delPoint(self, name: str, index: int = None, x: int = None, y: int = None):
        if self.config.get(name) is None:
            logger.error("不存在明文%s的数据集！")
            return False
        if index is not None:
            return self.config.get(name).pop(index)
        else:
            for _ in self.config.get(name):
                if _[0] == x and _[1] == y:
                    self.config.get(name).remove(_)
                    return _
