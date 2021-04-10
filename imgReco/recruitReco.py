import pytesseract
from ArkTagData.TagGetter import getRecruitAkaTag, getRecruitTag
import time


def _recruitIndex(index):
    # reco area:
    # block 140,40
    # 0 ->380, 364
    # 1 ->545, 364
    # 2 ->713, 364
    # 3 ->379, 436
    # 4 ->546, 436
    return [(380, 364), (545, 364), (713, 364), (379, 436), (546, 436)][index] + (140, 40)


def _recoRecruitSingle(recoStr: str):
    return recoStr.replace('\n', '').replace('\x0c', '').replace(' ', '')


def _recoRecruitSingle2(ark, index):
    image = ark.getScreenShot(*_recruitIndex(index))
    # '先锋干员',
    if ark.gameTemp.dingwei("recruit\\xfgy.png", image, 0.96):
        return "先锋干员"
    # '狙击干员',
    if ark.gameTemp.dingwei("recruit\\jjgy.png", image, 0.96):
        return "狙击干员"
    # '医疗干员',
    if ark.gameTemp.dingwei("recruit\\ylgy.png", image, 0.96):
        return "医疗干员"
    # '术师干员',
    if ark.gameTemp.dingwei("recruit\\ssgy.png", image, 0.96):
        return "术师干员"
    # '近卫干员',
    if ark.gameTemp.dingwei("recruit\\jwgy.png", image, 0.96):
        return "近卫干员"
    # '重装干员',
    if ark.gameTemp.dingwei("recruit\\zzgy.png", image, 0.96):
        return "重装干员"
    # '辅助干员',
    if ark.gameTemp.dingwei("recruit\\fzgy.png", image, 0.96):
        return "辅助干员"
    # '特种干员',
    if ark.gameTemp.dingwei("recruit\\tzgy.png", image, 0.96):
        return "特种干员"
    # '近战位',
    if ark.gameTemp.dingwei("recruit\\jzw.png", image, 0.96):
        return "近战位"
    # '远程位',
    if ark.gameTemp.dingwei("recruit\\ycw.png", image, 0.96):
        return "远程位"
    # '新手',
    if ark.gameTemp.dingwei("recruit\\xs.png", image, 0.96):
        return "新手"
    # '资深干员',
    if ark.gameTemp.dingwei("recruit\\zs.png", image, 0.96):
        return "资深干员"
    # '高级资深干员',
    if ark.gameTemp.dingwei("recruit\\gjzs.png", image, 0.96):
        return "高级资深干员"
    # '治疗',
    if ark.gameTemp.dingwei("recruit\\zl.png", image, 0.96):
        return "治疗"
    # '支援机械'    ##TBDC:先支援机械后支援
    if ark.gameTemp.dingwei("recruit\\zyjx.png", image, 0.96):
        return "支援机械"
    # '支援',
    if ark.gameTemp.dingwei("recruit\\zy.png", image, 0.96):
        return "支援"
    # '输出',
    if ark.gameTemp.dingwei("recruit\\shuchu.png", image, 0.96):
        return "输出"
    # '群攻',
    if ark.gameTemp.dingwei("recruit\\qg.png", image, 0.96):
        return "群攻"
    # '减速',
    if ark.gameTemp.dingwei("recruit\\js.png", image, 0.96):
        return "减速"
    # '生存',
    if ark.gameTemp.dingwei("recruit\\shengcun.png", image, 0.96):
        return "生存"
    # '防护',
    if ark.gameTemp.dingwei("recruit\\fh.png", image, 0.96):
        return "防护"
    # '削弱',
    if ark.gameTemp.dingwei("recruit\\xr.png", image, 0.96):
        return "削弱"
    # '位移',
    if ark.gameTemp.dingwei("recruit\\wy.png", image, 0.96):
        return "位移"
    # '控场',
    if ark.gameTemp.dingwei("recruit\\kc.png", image, 0.96):
        return "控场"
    # '爆发',
    #
    # '召唤',
    #
    # '快速复活',
    if ark.gameTemp.dingwei("recruit\\ksfh.png", image, 0.96):
        return "快速复活"
    # '费用回复',
    if ark.gameTemp.dingwei("recruit\\fyhf.png", image, 0.96):
        return "费用恢复"

    return None


def recognizeRecruit(ark):
    # Aka = getRecruitAkaTag()
    # s_t = time.time()
    # r = [Aka.where(i) for i in [_recoRecruitSingle(pytesseract.image_to_string(
    #     ark_main.getScreenShot(*_recruitIndex(i)), lang="chi_sim")) for i in range(5)]]
    # z = [True for _ in range(5)]
    # for i, v in enumerate(r):
    #     if v is None:
    #         r[i] = _recoRecruitSingle2(ark_main, i)
    #         z[i] = False

    Aka = getRecruitAkaTag()
    s_t = time.time()
    r = [_recoRecruitSingle2(ark, i) for i in range(5)]
    z = [True for _ in range(5)]
    for i, v in enumerate(r):
        if v is None:
            r[i] = Aka.where(
                _recoRecruitSingle(pytesseract.image_to_string(ark.getScreenShot(*_recruitIndex(i)), lang="chi_sim")))
            z[i] = False
    canrefresh = ark.gameTemp.dingwei("recruit\\refresh_ena.png", ark.getScreenShot(934, 371, 78, 55)) != []
    return {"tags": r,
            "recoV": z,
            "can_refresh": canrefresh,
            "cost": time.time() - s_t}
    # pytesseract.image_to_string(ark_main.getScreenShot(546, 436, 140, 40), lang="chi_sim")
    # pass


def recognizeCanRecruit(ark):
    _LM_CAN = None
    _RE_CAN = None
    if ark.gameTemp.dingwei("recruit\\recruit_ena.png", ark.getScreenShot(361, 655, 14, 14)):
        _LM_CAN = True
    elif ark.gameTemp.dingwei("recruit\\recruit_una.png", ark.getScreenShot(361, 655, 14, 14)):
        _LM_CAN = False

    if ark.gameTemp.dingwei("recruit\\recruit_ena.png", ark.getScreenShot(499, 655, 14, 14)):
        _RE_CAN = True
    elif ark.gameTemp.dingwei("recruit\\recruit_una.png", ark.getScreenShot(499, 655, 14, 14)):
        _RE_CAN = False
    return _LM_CAN, _RE_CAN, _LM_CAN and _RE_CAN
