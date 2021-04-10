import time


def _waitLooper(ark, template, xywh, sleepT):
    pass


def _callNotNull(callableObj):
    if callable(callableObj):
        return callableObj()
    return None


def _check_end_keep(delay):
    return time.time() + delay if delay > 0 else 0, delay < 0


def waitApRecovery(ark, delay=-1):
    # 开始战斗恢复理智结束检测
    end, keep = _check_end_keep(delay)
    while not ark.gameTemp.dingwei("on_atk_beg\\ap_recov.png", ark.getScreenShot(1044, 94, 78, 34)) and (
            True if keep else end > time.time()):
        time.sleep(0.2)
    return True


def waitVisitNextFriend(ark, func=None, delay=5):
    end, keep = _check_end_keep(delay)
    while not ark.gameTemp.dingwei("clue\\next.png", ark.getScreenShot(1115, 607, 139, 50)) and (
            True if keep else end > time.time()):
        time.sleep(0.2)
    _callNotNull(func)
    return True


def waitStartOperationAttack(ark, func=None, delay=-1):
    # 开始战斗图标检测
    end, keep = _check_end_keep(delay)
    while not ark.gameTemp.dingwei("on_atk_beg\\start_atk.png", ark.getScreenShot(1051, 517, 111, 61)) and (
            True if keep else end > time.time()):
        time.sleep(0.2)
    _callNotNull(func)
    return True


def waitExterminationEnd(ark, delay=40):
    end, keep = _check_end_keep(delay)
    while not ark.gameTemp.dingwei('main\\extr\\atk_end_at.png', ark.getScreenShot(904, 265, 88, 65)):
        if not (True if keep else end >= time.time()):
            return False
        time.sleep(2)
    return True


def waitGachaSkipBtn(ark, func=None, delay=-1):
    end, keep = _check_end_keep(delay)
    while not ark.gameTemp.dingwei("gacha\\skip.png", ark.getScreenShot(1193, 17, 64, 54)) and (
            True if keep else end > time.time()):
        time.sleep(0.2)
    _callNotNull(func)
    return True


def waitRecruitRefreshSuccess(ark, func=None, delay=5):
    end, keep = _check_end_keep(delay)
    while not ark.gameTemp.dingwei("recruit\\rec_ref_suc.png", ark.getScreenShot(1047, 98, 130, 26)) and (
            True if keep else end > time.time()):
        time.sleep(0.2)
    _callNotNull(func)
    return True


def waitCustomImageDetect(ark, imagePath, area, func=None, delay=5, slp=0.2, threshold=0.98):
    end, keep = _check_end_keep(delay)
    while not ark.gameTemp.dingwei(imagePath, ark.getScreenShot(*area), threshold=threshold) and (
            True if keep else end > time.time()):
        time.sleep(slp)
    _callNotNull(func)
    return True


def waitGetCreditItemOrNot(ark):
    end = time.time() + 3
    while True:
        if ark.gameTemp.dingwei("shop\\not_enough_credit.png", ark.getScreenShot(1149, 98, 95, 31)):
            return False
        elif ark.gameTemp.dingwei("shop\\credit_get.png", ark.getScreenShot(589, 142, 105, 30)):
            return True
        time.sleep(0.2)
        if end <= time.time():
            return False
