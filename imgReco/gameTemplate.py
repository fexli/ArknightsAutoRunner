import string
from utils.logger import root_logger as logger
from utils.utils import walkFile
import cv2
import numpy as np
import os


# 快速化图片检测前置
class GameTemplate(object):
    TEMPLATE = 0
    MAX = 1
    NOT_MATCH = 2

    def __init__(self, imgRootPath=None):
        self.__namelist__ = []
        self.__imgRootPath__ = imgRootPath
        if imgRootPath is not None:
            self.loadFolder(imgRootPath)

    def has(self, str_):
        return str_ in self.__namelist__

    def startswith(self, str_):
        ret = []
        for _ in self.__namelist__:
            if _.startswith(str_):
                ret.append(_)
        return ret

    def includewith(self, str_):
        ret = []
        for _ in self.__namelist__:
            if str_ in _:
                ret.append(_)
        return ret

    def loadFolder(self, root):
        for file in walkFile(root + "\\"):
            self.newTemplate(file, root + "\\" + file)

    def loadImage(self, imgPath):
        if os.path.isfile(imgPath):
            return cv2.imread(imgPath)
        raise ValueError

    def newTemplate(self, name, imgPath,
                    default_threshold=0.98,  # 默认识别度
                    onload=False,  # 是否直接加载
                    showlog=False):  # 是否显示成功添加
        if name[0] not in string.ascii_letters:
            logger.error(f'名字首位必须为字母字符:{name}')
            return None
        if not os.path.isfile(imgPath):
            logger.error("图片不存在:" + imgPath)
            return None
        if name not in self.__namelist__:
            temp = None
            if onload:
                temp = cv2.imread(imgPath)
            if isinstance(temp, type(None)) and onload:
                logger.error("未找到%s的图片[位于\'%s\']" % (name, imgPath))
                return None
            setattr(self, name, [temp, imgPath, default_threshold, onload])
            self.addName(name)
            if showlog:
                logger.debug("成功添加定位标志%s" % name)
        else:
            try:
                setattr(self, name, [cv2.imread(imgPath), imgPath, default_threshold, True])
                logger.warning("已覆盖名为%s的定位标志" % name)
            except:
                logger.warning('在覆盖标志时出现错误')
            return None

    def getTemplate(self, name) -> [np.ndarray, str, float, bool]:
        try:
            v = getattr(self, name)
            if not v[3]:
                v[0] = self.loadImage(v[1])
                v[3] = True
            return v
        except (NameError, AttributeError):
            return [None, None, None, None]
        except ValueError:
            logger.error("图像" + name + "路径不存在")
            return [None, None, None, None]

    def addName(self, name):
        self.__namelist__.append(name)

    def matchDifference(self, image, template, threshold=0.99, method=0):
        try:
            res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        except cv2.error as e:
            logger.error(e)
            return []
        gps = []
        if method == self.TEMPLATE:
            loc = np.where(res >= threshold)
            for pt in zip(*loc[::-1]):
                gps.append(pt)
            return gps
        if method == self.MAX:
            return np.max(res), np.where(res == np.max(res))
        if method == self.NOT_MATCH:
            return res

    def dingwei(self, name, image, threshold=None):
        template, tbd, default_th, tbd = self.getTemplate(name)
        if template.all() is None:
            logger.error("未找到名为%s的定位标志" % name)
            return []
        else:
            threshold = threshold or default_th
            return self.matchDifference(image, template, threshold, method=self.TEMPLATE)
