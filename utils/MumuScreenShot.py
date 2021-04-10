# from yys_define import *
import sys
from utils.logger import root_logger as logger
import win32gui
import qimage2ndarray
from PyQt5.QtWidgets import QApplication
# from config.RootData import RootData
app = QApplication(sys.argv)
screen = QApplication.primaryScreen()


# 游戏自动化执行类
class hwndHandle():
    __hwnd_title = dict()
    hwnds = []
    gamenum = 0

    def __init__(self, name='明日方舟 - MuMu模拟器'):
        self._name = name
        _selectGame = [-1, -1]
        self.hwnds = self.get_all_hwnds(self._name)
        self.gamenum = self.hwnds.__len__()
        self.windows = self.get_all_window_info()
        self._selectGame = [[-1, -1, -1, -1, -1, -1], -1]
        if self.gamenum == 0:
            pass
        elif self.gamenum == 1:
            self._selectGame = [self.windows[0], self.hwnds[0]]
        else:
            self.selectHandle(0)

    def __str__(self):
        ret = {'name': self._name, 'select': self._selectGame}
        return 'multigame(' + str(ret) + ')'

    def regetgame(self, hwndnum=0):
        self.hwnds = []
        self.gamenum = 0
        self.hwnds = self.get_all_hwnds(self._name)
        self.gamenum = self.hwnds.__len__()
        self.windows = self.get_all_window_info()
        if self.gamenum == 1:
            self._selectGame = [self.windows[0], self.hwnds[0]]

        elif self.gamenum == 0:
            self._selectGame = [-1, -1]
        else:
            self.selectHandle(hwndnum)

    def __get_all_hwnd(self, hwnd, nothing):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
            self.__hwnd_title.update({hwnd: win32gui.GetWindowText(hwnd)})

    def get_all_hwnds(self, name=None, prefix_mode=False):
        hwnds = []
        self.__hwnd_title = dict()
        win32gui.EnumWindows(self.__get_all_hwnd, 0)
        if name == None:
            name = self._name
        if name == '':
            return self.__hwnd_title
        if prefix_mode:
            for h, t in self.__hwnd_title.items():
                if name in t:
                    hwnds.append(h)
        else:
            for h, t in self.__hwnd_title.items():
                if t == name:
                    hwnds.append(h)
        hwnds.sort(reverse=True)
        return hwnds

    def printhwnddict(self):
        print(self.__hwnd_title)

    def get_all_window_info(self):  # xmin ymin xmax ymax xsize ysize
        handle = self.hwnds
        if isinstance(handle, (list)):
            windows = []
            for item in range(handle.__len__()):
                handlenow = handle[item]
                window = win32gui.GetWindowRect(handlenow)
                window2 = list(window)
                xcon = window[2] - window[0]
                ycon = window[3] - window[1]
                window2.append(xcon)
                window2.append(ycon)
                windows.append(window2)
            return windows
        else:
            logger.error("handle %s 不存在" % handle)
            return False

    def updateWindowDirection(self):
        self._selectGame[0] = self.get_window_info(self._selectGame[0])
        return True

    def getSelectGame(self, *hwnd):
        if hwnd:
            self.selectHandle(hwnd[0])
        else:
            self.updateWindowDirection()
        return self._selectGame

    def getSelectGameNow(self):
        return self._selectGame

    def selectHandle(self, handle):
        if isinstance(handle, int):
            if handle >= 100:
                if handle in self.hwnds:
                    logger.debug("Find handle:%d" % handle)
                    self._selectGame = self.get_window_info(handle)
                    return self
                else:
                    logger.error("未找到该句柄对应的客户端！")
                    self._selectGame = [-1, -1]
                    return False
            elif handle <= 99:
                if handle <= self.hwnds.__len__() - 1:
                    self._selectGame = [self.windows[handle], self.hwnds[handle]]
                    return self
                else:
                    logger.error("句柄超过全部句柄数量！")
                    self._selectGame = [-1, -1]
                    return False
        else:
            logger.error("expect type:int got %s instead" % type(handle))

    def get_window_info(self, hwndfind=0):  # xmin ymin xmax ymax xsize ysize
        if hwndfind == 0:
            wdname = u'明日方舟 - MuMu模拟器'
            handle = win32gui.FindWindow(0, wdname)  # 获取窗口句柄
        else:
            handle = hwndfind
        if handle == 0:
            logger.error('未检测到明日方舟！', 'RED')
            return None
        else:
            window = win32gui.GetWindowRect(handle)
            window2 = list(window)
            xcon = window[2] - window[0]
            ycon = window[3] - window[1]
            window2.append(xcon)
            window2.append(ycon)
            return window2, handle


mumu_handler = hwndHandle("明日方舟 - MuMu模拟器")


# 获取截图(new method)
def getscreenshot(xinwindow=0, yinwindow=0, w=1280, h=720, hwnd='dft', fullscreen=False):
    global screen
    if hwnd == 'dft':
        hwnd = mumu_handler.getSelectGameNow()[1]
    if not fullscreen:
        img = screen.grabWindow(hwnd, x=xinwindow, y=yinwindow + 36, width=w, height=h).toImage()
    else:
        img = screen.grabWindow(hwnd).toImage()
    img = qimage2ndarray.rgb_view(img, byteorder='little')
    return img
