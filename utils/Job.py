import threading
import ctypes
import inspect


# 多线程 可传返回参数
class Job(threading.Thread):
    def __init__(self, target=None, args=(), **kwargs):
        super(Job, self).__init__()
        self.__flag = threading.Event()  # 用于暂停线程的标识
        self.__flag.set()  # 设置为True
        self.__running = threading.Event()  # 用于停止线程的标识
        self.__running.set()  # 将running设置为True
        self.is_running = False
        self._target = target
        self._args = args
        self._kwargs = kwargs
        self.__result__ = None

    def wait(self):
        self.__flag.wait()

    def pause(self):
        self.__flag.clear()  # 设置为False, 让线程阻塞

    def resume(self):
        self.__flag.set()  # 设置为True, 让线程停止阻塞

    def stop(self):
        self.__flag.set()  # 将线程从暂停状态恢复, 如何已经暂停的话
        self.__running.clear()  # 设置为False
        self.is_running = False

    def set_target(self, target, args=(), **kwargs):
        if self.is_running:
            raise RuntimeError("线程正在运行中，无法更改目标函数。")
        self._target = target
        self._args = args or self._args
        self._kwargs = kwargs or self._kwargs

    def run(self):
        if self._target is None:
            return
        self.is_running = True
        self.__result__ = self._target(*self._args, **self._kwargs)
        self.is_running = False

    def get_result(self, nJoin=False):
        if nJoin:
            self.join()  # 当需要取得结果值的时候阻塞等待子线程完成
            return self.__result__
        else:
            try:
                ret = self.__result__
                return ret
            except:
                return None


# 多线程安全停止 - 前置
def _async_raise(tid, exctype):
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        pass
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


# 多线程安全停止
def stop_thread(thread):
    try:
        thread.resume()
    except:
        pass
    _async_raise(thread.ident, SystemExit)
