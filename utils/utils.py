import time
import os
import random
from .logger import root_logger as logger


def time_sleep(t, randomdel=28, showdebug=False):
    rand_timedelay = random.randint(0, randomdel) / 1000
    time_alldelay = t + rand_timedelay
    if showdebug:
        logger.debug('sleep:%.4fs' % time_alldelay)
    time.sleep(time_alldelay)


def getLogFileName():
    return "Ark-" + time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime()) + ".log"


def removeItemFromList(List, Item):
    return [i for i in List if i != Item]


def removeItemsFromList(List, *Item):
    for _ in Item:
        List = removeItemFromList(List, _)
    return List


def _check_type(base):
    if not isinstance(base, (type, type(None))):
        raise TypeError("base type need type or NoneType")
    return True


class PushableDict(dict):
    def __init__(self, kv: (dict, list) = None, base: type = None):
        _check_type(base)
        if kv is not None:
            super(PushableDict, self).__init__(kv) if base is None else super(PushableDict, self) \
                .__init__(zip(kv, [base() for _ in kv]))
        else:
            super(PushableDict, self).__init__()
        self.__base__ = base

    def set_base(self, base):
        _check_type(base)
        self.__base__ = base
        return self

    def has(self, key):
        return key in self.keys()

    def new(self, key):
        self.update({key: self.__base__()})

    def push(self, key, value, method=list.append, create: bool = False):
        if key in self.keys():
            try:
                method(self.get(key), value)
                return True
            except Exception:
                return False
        elif create:
            if self.__base__ is None:
                return False
            self.update({key: self.__base__()})
            return self.push(key, value, method, create)

    def where(self, value):
        for _ in self:
            if value in self.get(_):
                return _

    def wheres(self, values):
        ret = []
        for value in values:
            ret.append(self.where(value))
        return ret


# 遍历文件夹
def walkFile(file):
    ret = []
    for root, dirs, files in os.walk(file):

        # root 表示当前正在访问的文件夹路径
        # dirs 表示该文件夹下的子目录名list
        # files 表示该文件夹下的文件list

        # 遍历文件
        for f in files:
            ret.append(os.path.join(root[len(file):], f))

        # # 遍历所有的文件夹
        # for d in dirs:
        #     print(os.path.join(root, d))
    return ret


# 区域格式化位置
def region_format(xstart: int, ystart: int, xlen: int, ylen: int, dingwei: list, format_type: str = 'POS', x_id_max=0,
                  y_id_max=0):
    ret = []
    for item in dingwei:
        x_p = (item[0] - xstart) // xlen
        y_p = (item[1] - ystart) // ylen
        if (x_p, y_p) not in ret:
            ret.append((x_p, y_p))
    if format_type == 'POS':
        return ret
    if format_type == 'ID':
        retstr = ''
        for y in range(y_id_max):
            for x in range(x_id_max):
                if (x, y) in ret:
                    retstr += '1'
                else:
                    retstr += '0'
        return retstr


def randomstr(len_=8, spark=True, randSet=None):
    import random
    import string
    if randSet:
        rand = str(randSet)
    else:
        rand = string.ascii_letters + '0123456789' + ('-_' if spark else '')
    r = ''
    for _ in range(len_):
        r += random.choice(rand)
    return r
