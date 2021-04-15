import random
from utils.logger import root_logger as logger
from utils.utils import time_sleep


class Clicker(object):
    def __init__(self, adb):
        self.adb = adb
        self.rx = (-10, 10)
        self.ry = (-10, 10)

    def setRandom(self, rx, ry):
        self.rx = rx
        self.ry = ry

    def mouse_click(self, x, y, rx=None, ry=None, t=0, at=0, condition=True):
        if condition:
            if rx is None:
                x += random.randint(*self.rx)
            else:
                x += random.randint(*rx)
            if ry is None:
                y += random.randint(*self.ry)
            else:
                y += random.randint(*ry)
            x, y = int(x), int(y)
            logger.debug("点击坐标:({},{})".format(x, y), backlevel=5)
            time_sleep(at)
            command = "input tap {} {}".format(x, y)
            self.adb.run_device_cmd(command)
            time_sleep(t)
        return condition

    def dragTo(self, x1, y1, x2, y2, duration=None, r=None, f_back=5):
        if r is None:
            x1 += random.randint(*self.rx)
            x2 += random.randint(*self.rx)
            y1 += random.randint(*self.ry)
            y2 += random.randint(*self.ry)
        else:
            x1 += random.randint(*r[0])
            x2 += random.randint(*r[0])
            y1 += random.randint(*r[1])
            y2 += random.randint(*r[1])
        logger.debug("滑动初始坐标:({},{}) 结束坐标({} {})".format(x1, y1, x2, y2), backlevel=f_back)
        command = "input swipe {} {} {} {} ".format(x1, y1, x2, y2)
        if duration is not None:
            command += str(int(duration))
        self.adb.run_device_cmd(command)

    def dragRel(self, x1, y1, dx, dy, duration=None, r=None, f_back=6):
        x2 = x1 + dx
        y2 = y1 + dy
        # print(x1, x2, y1, y2)
        self.dragTo(x1, y1, x2, y2, duration=duration, r=r, f_back=f_back)

    def input_text(self, text):
        self.adb.run_device_cmd(f'input keyboard text {text}')
