import sys

import numpy as np
from PIL import Image
from typing import Tuple
import cv2
from . import imgops
from . import minireco
from . import resources
from config.RootData import RootData
from ArkTagData.TagGetter import getItemTag, getDropList, getActivityOpen,getMapCost
from utils.logger import root_logger as logger
from utils.utils import region_format
from utils.utils import PushableDict
from . import itemReco
from ArkType.StageExcel import StageDropInfo


@RootData.cache("recognizer")
def load_data() -> Tuple[
    minireco.MiniRecognizer, minireco.MiniRecognizer, minireco.MiniRecognizer, minireco.MiniRecognizer]:
    # if not RootData.has("recognizer"):
    reco = minireco.MiniRecognizer(resources.load_pickle('minireco/NotoSansCJKsc-Medium.dat'))
    reco2 = minireco.MiniRecognizer(resources.load_pickle('minireco/Novecentosanswide_Medium.dat'))
    num = minireco.MiniRecognizer(resources.load_pickle('minireco/NotoSansCJKsc-DemiLight-nums.dat'))
    camp = minireco.MiniRecognizer(resources.load_pickle('minireco/Novecentosanswide_Medium.dat'))
    # RootData.set("recognizer", (reco, reco2,))
    return reco, reco2, num, camp
    # return RootData.get("recognizer")


known_fix_data = [('LQ', "LS"), ('PR-C-Z', 'PR-C-2'), ('0D-', 'OD-')]


def fix_known_data(opidtext):
    if opidtext.endswith('-'):
        opidtext = opidtext[:-1]
    opidtext = opidtext.upper()
    for replacer in known_fix_data:
        opidtext = opidtext.replace(*replacer)
    return opidtext


def recognizeOperation(image, map_dict=None) -> Tuple[str, str]:
    if not map_dict:
        map_dict = getMapCost()
    opidtext = fix_known_data(load_data()[1].recognize2(image, subset='0123456789abcdefghijklmnopqrstuvwxyz-')[0])

    where_ = map_dict.where(opidtext)
    if where_:
        return opidtext, where_
    # 无法识别，尝试使用tesseract
    logger.warning("无法识别地图信息" + opidtext)
    debug_ret = []
    import pytesseract
    for index in range(10):
        ret = pytesseract.image_to_string(image, lang="eng") \
            .replace("\n", "").replace("\x0c", "")
        where_ = map_dict.where(ret)
        debug_ret.append(ret)
        if where_:
            logger.debug("识别信息:%s" % str(debug_ret))
            return ret, where_

    logger.error("在10次识别后依旧无法识别出当前关卡信息。")
    logger.debug("识别信息:%s" % str(debug_ret))
    return "", ""


def recognizePrtsStatus(ark) -> str:
    if ark.gameTemp.dingwei("on_atk_beg\\prts_dis.png", ark.getScreenShot(1129, 570, 71, 47), 0.96):
        if ark.gameTemp.dingwei("on_atk_beg\\prts_lock.png", ark.getScreenShot(1044, 573, 48, 41), 0.96):
            return "LOCK"
        return "DISABLE"
    return "ENABLE"


def recognizeEndStar(ark) -> int:
    v = ark.gameTemp.dingwei("on_atk_end\\end_dot.png", ark.getScreenShot(169, 496, 220, 63), 0.8)
    return len(region_format(3, 13, 77, 62, v))


def recognizeApSuplyItems(ark, quantity=True):
    pass


def recognizeEndItems(ark, stageCode, quantity=True):
    drop_list = getDropList(stageCode)
    for i in getActivityOpen()[1]:
        drop_list.add((i, getItemTag()['items'][i].get('name', "未知物品:" + i)))
    # drop_list = list(drop_list)
    # return drop_list
    screen = ark.getScreenShot(470, 520, 800, 160)
    drop_reco = []
    for item, name in drop_list:
        try:
            rep, where = ark.gameTemp.matchDifference(screen,
                                                      cv2.resize(
                                                          ark.gameTemp.getTemplate("lootitem\\" + item + ".png")[0],
                                                          itemReco.STAGE_DROP)[29:29 + 46, 34:34 + 68], method=1)
        except cv2.error as cverr:
            logger.warning(f"处理掉落物'{name}'失败:(code={cverr.code}){cverr.err} in function '{cverr.func}'")
            continue
        y, x, num = -1, -1, -1
        if rep >= 0.9:
            y, x = int(where[0]), int(where[1])
            x += 26
            y += 63
            if quantity:
                imgraw = Image.fromarray(screen[y:y + 27, x:x + 53])
                numimg = imgops.crop_blackedge2(imgraw, 120)
                if numimg is None or numimg.size < (5, 5):
                    numimg = imgops.clear_background(imgraw, threshold=180)
                # cv2.imshow("d",np.asarray(numimg)); cv2.waitKey(0)
                img = imgops.clear_background(numimg, threshold=120)
                # cv2.imshow("i", np.asarray(img)); cv2.waitKey(0)
                reco = ark.reconizerN.recognize2(img, subset="0123456789万")
                try:
                    num = int(reco[0]) if reco != '' else 0
                except:
                    num = 0
            else:
                num = -1
        err = rep > 0.9 and num <= 0
        if err:
            logger.warning(f"识别到物品\"{name}\"数量出现异常，已置零，该物品将不计入统计中")
        # drop_reco.append([name, rep > 0.9, rep, [x, y], num])
        drop_reco.append({"name": name,
                          "have": rep > 0.9,
                          "_acq": rep,
                          "_pos": (x, y),
                          "quantity": num,
                          "error": err})
    return drop_reco


def recognizeEndItemDropType(screen, x):
    # force_y = 230
    def getDistance(rgb1: tuple, rgb2: np.ndarray):
        b1, g1, r1 = rgb1
        b2, g2, r2 = int(rgb2[0]), int(rgb2[1]), int(rgb2[2])
        return (b2 - b1) ** 2 + (g2 - g1) ** 2 + (r2 - r1) ** 2

    min_type = 254
    min_dist = 2 ** 18
    for k, v in StageDropInfo.dropTypeColor.items():
        d = getDistance(v, screen[151, x + 40])
        if d < min_dist:
            min_dist = d
            min_type = k
    return min_type


def recognizeEndItemsWithTag(ark, stageCode_or_dropList, quantity=True):
    def removeClosePos(gps: list):
        if len(gps) <= 1:
            return gps
        gps.sort()
        final = [gps[0]]
        prev_x = gps[0][0]
        for _x, _y in gps:
            if -7 < prev_x - _x < 7:
                continue
            prev_x = _x
            final.append((_x, _y,))
        return final

    if isinstance(stageCode_or_dropList, str):
        drop_list = getDropList(stageCode_or_dropList)
    else:
        drop_list = stageCode_or_dropList
    for i in getActivityOpen()[1]:
        drop_list.add((i, getItemTag()['items'][i].get('name', "未知物品:" + i)))
    screen = ark.getScreenShot(470, 520, 800, 160)
    drop_reco = []
    for item, name in drop_list:
        dumped = False
        try:
            gps = ark.gameTemp.matchDifference(screen, cv2.resize(
                ark.gameTemp.getTemplate("lootitem\\" + item + ".png")[0], itemReco.STAGE_DROP)[29:29 + 46, 34:34 + 68]
                                               , threshold=0.9)
        except cv2.error as cverr:
            try:
                gps = ark.gameTemp.matchDifference(screen,
                                                   ark.gameTemp.getTemplate("lootitem\\dumped\\" + item + ".png")[0]
                                                   [29:29 + 46, 34:34 + 68], threshold=0.9)
                dumped = True
            except (cv2.error, TypeError):
                logger.warning(f"处理掉落物'{name}<{item}>'失败:(code={cverr.code}){cverr.err} in function '{cverr.func}'")
                continue
        gps = removeClosePos(gps)
        for x, y in gps:
            if dumped:
                y = 28
            # 检测所有位置的掉落信息，分别根据不同位置判断不同掉落属性dropType
            num = -1
            x += 26
            y += 63
            if quantity:
                imgraw = Image.fromarray(screen[y:y + 27, x:x + 53])
                # cv2.imshow('r', np.array(imgraw))
                # cv2.waitKey(0)
                numimg = imgops.crop_blackedge2(imgraw, 150)
                # cv2.imshow('n', np.array(numimg))
                # cv2.waitKey(0)
                if numimg is None or numimg.size < (5, 5):
                    numimg = imgops.clear_background(imgraw, threshold=180)
                img = imgops.clear_background(numimg, threshold=120)
                # cv2.imshow('g', np.array(img))
                # cv2.waitKey(0)
                reco = ark.reconizerN.recognize2(img, subset="0123456789万")
                # print(reco)
                try:
                    num = int(reco[0]) if reco != '' else 0
                except:
                    num = 0
            else:
                num = -1
            err = num <= 0
            if err:
                logger.warning(f"识别到物品\"{name}\"数量出现异常({num})，已置零，该物品将不计入统计中")
            else:
                drop_reco.append({"name": name,
                                  "have": True,
                                  "_acq": 0.9,
                                  "type": recognizeEndItemDropType(screen, x),
                                  "_pos": (x, y),
                                  "quantity": num,
                                  "error": err})
    return drop_reco


def recognizeCampaignNum(ark):
    # TODO:检察当前位置
    image = imgops.clear_background(Image.fromarray(ark.getScreenShot(101, 638, 190, 42)), 200)
    a = ark.reconizerN2.recognize2(image, subset="0123456789x")[0].replace('x', "/")
    try:
        now, max_ = a.split("/")
        success = True
    except ValueError:
        now, max_ = 0, 0
        success = False
    return {"success": success,
            "now": int(now),
            "max": int(max_)}


def recognizeExterminationDetail(ark):
    pass


def recognizeBeforeOperationInte(ark):
    try:
        u, v = ark.reconizerC.recognize2(imgops.clear_background(
            Image.fromarray(ark.getScreenShot(1120, 20, 150, 40)), 130), subset="0123456789/")[0].split("/")
    except ValueError:
        u, v = -1, -1
    return int(u), int(v)  # now,max
