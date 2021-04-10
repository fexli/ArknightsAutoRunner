import sys
import os
from functools import wraps
from utils.logger import root_logger as logger
import time


def get_len_or(v, default=0):
    try:
        return len(v)
    except:
        return default


class RootData:
    __data__ = dict()

    # __update__ = False

    @staticmethod
    def clearCache(key: str = None):
        if key is None:
            RootData.__data__.clear()
            return True
        if RootData.has(key):
            RootData.__data__.pop(key)
            return True
        return False

    @staticmethod
    def cache(arg, update=False, max_cache_time=-1):
        def _write2cache(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if isinstance(arg, str):
                    if update or not RootData.has(arg):
                        ret = func(*args, **kwargs)
                        cache_time = 0 if max_cache_time < 0 else time.time() + max_cache_time
                        RootData.set(arg, ret, cache_time)
                        return ret
                    else:
                        return RootData.get(arg)
                else:
                    logger.warning("cache can't store name for type of %s" % arg.__class__.__name__)
                    return func(*args, **kwargs)

            return wrapper

        return _write2cache

    @staticmethod
    def set(key, value, cache_time=0):
        return RootData.__data__.update({key: (value, cache_time,)})

    @staticmethod
    def get(key, default=None):
        ret = RootData.__data__.get(key, None)
        if get_len_or(ret, 0) != 2:
            return default
        return ret[0]

    @staticmethod
    def has(key):
        if key in RootData.__data__.keys():
            if RootData.__data__.get(key)[1] > time.time() or RootData.__data__.get(key)[1] == 0:
                return True
        return False

    @staticmethod
    def __getattr__(item, default=None):
        return RootData.get(item, default)


if not RootData.has("config_registered"):
    CONFIG = {"device/adb_auto_connect": "127.0.0.1:7555",
              "device/try_emulator_enhanced_mode": True,
              "device/cache_screenshot": True,
              "device/package_name": "com.hypergryph.arknights",
              "device/activity_name": "com.u8.sdk.U8UnityContext",
              "device/adb_binary": ".\\ADB\\win32\\adb.exe"}
    for k in CONFIG:
        RootData.set(k, CONFIG[k])
    bundled = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
    if bundled:
        root = sys._MEIPASS
        CONFIG_PATH = os.path.join(root, 'config')
    else:
        CONFIG_PATH = os.path.realpath(os.path.dirname(__file__))
        root = os.path.realpath(os.path.join(CONFIG_PATH, '..'))

    RootData.set('SCREEN_SHOOT_SAVE_PATH', os.path.join(root, 'screenshot'))
    RootData.set("ADB_ROOT", os.path.join(root, 'ADB', sys.platform))
    RootData.set("CONFIG_PATH", CONFIG_PATH)
    RootData.set("ROOT", root)
    RootData.set("ADB_SERVER", ("127.0.0.1", 5037))
    RootData.set("use_archived_resources", False)
    RootData.set("config_registered", True)
