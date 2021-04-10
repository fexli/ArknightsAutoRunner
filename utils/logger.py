import sys
import inspect
import os
import time
from .logcolor import Color as color
from PyQt5 import QtWidgets
from datetime import datetime


def get_cur_info(f_back_level=1):
    frame = sys._getframe()
    for i in range(f_back_level):
        frame = frame.f_back
    info = inspect.getframeinfo(frame)
    return {"function": info.function,
            "lineno": info.lineno,
            "filepath": info.filename,
            "filename": os.path.basename(info.filename)}


# 格式化时间输出
def printer(str_, flush=False, back_l=4, show_=True):
    cur = get_cur_info(back_l)
    if show_:
        str_out = Logger.time_now() + "(\"{filename}\",in {function} line {lineno})".format(**cur) + str_
    else:
        str_out = Logger.time_now() + str_

    if flush == False:
        print(str_out)
        sys.stdout.flush()
    else:
        sys.stdout.write(str_out + '\r')
        sys.stdout.flush()
    return str_out


# 简单记录
class Logger(object):
    _needcls = True
    _Debug = True
    root = None
    color = color

    def __init__(self, needcls=True, _splogin=False):
        if self._needcls and needcls:
            os.system('cls')

        self.logging = []  # 最简日志输出
        self.color_now = ''  # 当前颜色配置
        self.need_printto = False
        self.pyqtprint_html = ''
        self._splogin = _splogin
        self.start_t = -1
        self._MSGclient_autosend = False

    @staticmethod
    def get():
        return Logger.root

    def splogin(self, *select):
        if select:
            self._splogin = bool(select[0])
        return self._splogin

    def bandPyQtTextOutput(self, qttext: QtWidgets.QTextEdit):
        if isinstance(qttext, QtWidgets.QTextEdit):
            self.printTo = qttext
            self.need_printto = True

    def markTime(self):
        if self.start_t != -1:
            start = self.start_t
            self.start_t = time.time()
            return time.time() - start
        else:
            self.start_t = time.time()
            return 0

    def setDebug(self, selection=True):
        if selection == True:
            self._Debug = True
        elif selection == False:
            self._Debug = False
        else:
            self.error("Unknown Type!\nusing True/False")

    def log2file(self, filename, prefix=''):
        if (isinstance(filename, str)):
            if not os.path.exists(filename):
                file = open(filename, 'w', encoding='utf-8')
                file.write('#')
                file.write(prefix)
                file.write('\n')
                file.close()
            file = open(filename, 'a', encoding='utf-8')
            file.write('Log at ')
            file.write(LogTime.tools.gettime_YMD())
            file.write('\n')
            # file.write(self.logging.encode())
            for i in self.logging:
                file.write(str(i))
                file.write('\n')
            file.write('\n')
            file.close()
        else:
            self.error('输入目录非法', colors='RED')
            return 0

    def log2logging(self, log):
        self.logging.append(self.time_now() + log)
        # if self._MSGclient_autosend:
        #     msgserver.sendMSG_toserver(self.time_now() + log)
        #     # TODO:

    def colors(self, colorsn):
        if hasattr(color.print, colorsn):
            self.color_now = getattr(color.print, colorsn)
        else:
            self.color_now = "\033[1;37m"

    lamb_s = lambda self, colors: "<font color='" + colors.lower() + "' size='3'>" if colors != '' else ''
    lamb_e = lambda self, colors: '</font><br>' if colors != '' else '<br>'

    def removeCMDcolorFormat(self, opt: str):
        if isinstance(opt, str):
            for item in color.print.list:
                opt = opt.replace(getattr(color.print, item), '')
        else:
            print(type(opt))
        return opt

    def chgColorFormat(self, opt: str):
        if isinstance(opt, str):
            for item in color.print.list:
                try:
                    opt = opt.replace(getattr(color.print, item), getattr(color.print.html, item))
                except:
                    pass
        else:
            print(type(opt))
        return opt

    def time_now(*self):
        # return "[" + str(time.strftime("%H:%M:%S", time.localtime())) + str(round(time.time() % 1, 3))[1:] + "]"
        return f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}]"

    def debug(self, output, colors='', log2logging=True, flush=False, backlevel=4):
        if self._Debug:
            self._log(output, colors, 'CYAN', "[Debug]", flush, log2logging, backlevel=backlevel)

    def _log(self, output, colors, prefcolor, prefix, flush=False, log2logging=False, backlevel=4):
        self.colors(colors)
        if self._splogin:
            if colors == '':
                colors = 'BLACK'
            printer(
                getattr(color.print.html, prefcolor) + prefix + color.print.html.END + getattr(color.print.html,
                                                                                               colors) + self.chgColorFormat(
                    str(output)) + color.print.html.END + '<br>', flush, back_l=backlevel, show_=self._Debug)
        else:
            printer(getattr(color.print, prefcolor) + prefix + color.print.END + self.color_now + str(
                output) + color.print.END, flush, back_l=backlevel, show_=self._Debug)
        if log2logging:
            self.log2logging(prefix + ("(\"{filename}\",in {function} line {lineno})".format(
                **get_cur_info(backlevel-1)) if self._Debug else '') + str(output))
        if self.need_printto:
            self.pyqtprint_html = self.pyqtprint_html + self.time_now() + "<font color='" + prefcolor.lower() + \
                                  "' size='3'>" + prefix + "</font>" + self.lamb_s(
                colors) + str(output) + self.lamb_e(colors) + '\n'
            self.printTo.setHtml(self.pyqtprint_html)

    def help(self, output, colors='', flush=False):
        self._log(output, colors, 'DARKCYAN', "[HELP]", flush, False)

    def warning(self, output, colors='', flush=False, log2logging=True):
        self._log(output, colors, 'RED', "[WARNNG]", flush, log2logging)

    def notice(self, output, colors='', flush=False, log2logging=True):
        self._log(output, colors, 'YELLOW', "[NOTICE]", flush, log2logging)

    def error(self, output, colors='', flush=False, log2logging=True):
        self._log(output, colors, 'RED', "[ERRORS]", flush, log2logging)

    def system(self, output, colors='', flush=False, log2logging=True):
        self._log(output, colors, 'GREEN', "[SYSTEM]", flush, log2logging)

    def common(self, output, colors='', flush=False, log2logging=True):
        self.colors(colors)
        if self._splogin:
            if colors == '':
                colors = 'BLACK'
            printer(getattr(color.print.html, colors) + self.chgColorFormat(
                str(output)) + color.print.html.END + '<br>', flush, back_l=3)
        else:
            printer(self.color_now + output + color.print.END, flush, back_l=3)
        if log2logging:
            self.log2logging(str(output))
        if self.need_printto:
            self.pyqtprint_html = self.pyqtprint_html + self.time_now() + self.lamb_s(
                colors) + str(output) + self.lamb_e(colors) + '\n'

            self.printTo.setHtml(self.pyqtprint_html)


root_logger = Logger(needcls=False)
Logger.root = root_logger


# 记录时间
class LogTime():
    time_now = 0

    def gettime(*self):
        return time.time()

    class tools():
        def gettime_YMDHMS(*self):
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        def gettime_YMDH(*self):
            return time.strftime("%Y-%m-%d %H", time.localtime())

        def gettime_HMS(*self):
            return time.strftime("%H:%M:%S", time.localtime())

        def gettime_YMD(*self):
            return time.strftime("%Y-%m-%d", time.localtime())
