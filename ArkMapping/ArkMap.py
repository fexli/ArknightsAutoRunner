import os
import json
from utils.logger import root_logger as logger
from imgReco.mapReco import getCurrentEpisode
import math
import time
from config.Statics import ACTIVITY_MAP, NORMAL_MAP, ArkMap_RECO, ArkMap_ACTIVITY


def error_map(targStage, targMap):
    logger.error(f"关卡'{targStage}'在地图'{targMap}'中但是没有适配进入模式，请在ArkMap中进行适配后再次运行")
    return False


class ArkMap(object):
    RECO = ArkMap_RECO

    def __init__(self, ark, data_path="./ArkMapping/Map/root.json", ):
        self._data_path = data_path
        self.__ark = ark
        if os.path.exists(data_path):
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    self.root = json.load(f)
                # TODO:LOAD MAPS
                self.maps = {}
            except Exception as e:
                logger.error(f"invalid data {data_path}:{str(e)}")
        else:
            self.root = {"maps": []}
            self.maps = {}
        if self.root["maps"]:
            fold = os.path.dirname(self._data_path) + '\\'
            for map in self.root["maps"]:
                with open(fold + map + ".json", 'r', encoding="utf-8") as f:
                    self.maps.update({map: json.load(f)})

    def getMainMapPosition(self):
        # map_main上主线章节地图位置
        image = self.__ark.getScreenShot(0, 348, 1280, 44)
        ret = []
        for _ in self.__ark.gameTemp.startswith("main\\map\\ch"):
            gps = self.__ark.gameTemp.dingwei(_, image, 0.9)
            if gps:
                x, y = gps[0]
                x += 105
                y += 348 - 20
                ret.append([int(_[-5]), (x, y)])
        return ret

    def checkMapClose(self, target: int):
        dist = []
        map_ = self.getMainMapPosition()
        for i, pos in map_:
            if target - i == 0:
                return [i, pos]
            dist.append(abs(target - i))
        return map_[dist.index(min(dist))]

    def getStageInfo(self, stageName: str):
        if stageName is None:
            return [None]
        for name, data in self.maps.items():
            if stageName in [i for i, v in data['stages']]:
                return name, data
        logger.error(f"未知关卡名称'{stageName}'，请检查！")

    def getMapStageInfo(self, name: str):
        # 获取当前地图上name的关卡
        _stage_list = self.__ark.gameTemp.startswith(f"main\\map\\{name}\\")
        image = self.__ark.getScreenShot()
        rect = []
        for stage in _stage_list:
            gps = self.__ark.gameTemp.dingwei(stage, image, threshold=0.96)
            if gps:  # 有输出，证明存在关卡
                rect.append([stage, gps[0]])
        return rect

    def stageInSameMap(self, stage1, stage2, mapName=None):
        if mapName is not None:
            if stage2 in [name for name, pos in self.maps[mapName]["stages"]]:
                return True
            return False
        for mapName, data in self.maps.items():
            stagelist = [name for name, pos in data["stages"]]
            if stage1 in stagelist:
                if stage2 in stagelist:
                    return True
                return False
        logger.error(f"{stage1} not in the MapData")
        return False

    def getDistanceBetweenStage(self, mapName, stage1, stage2):
        s = self.maps[mapName]["stages"]
        n = [i for i, v in s]
        sx1, sy1 = s[n.index(stage1)][1]
        sx2, sy2 = s[n.index(stage2)][1]
        return sx2 - sx1, sy2 - sy1

    def moveStageInMap(self, mapName, stage1, stage2, error=True):
        # 承接changestageinmap，在识别到两个stage基础上进行stage内移动
        rect = self.getMapStageInfo(mapName)
        rect_stage = [os.path.basename(i)[:-4] for i, v in rect]
        assert rect != []
        if error:
            stage1 = rect_stage[0]
        else:
            assert stage1 in rect_stage
        x, y = rect[rect_stage.index(stage1)][1]
        # print(rect, stage1, stage2, rect_stage)
        dx, dy = self.getDistanceBetweenStage(mapName, stage1, stage2)
        if 0 < dx + x < 1240 and 50 < dy + y < 618:
            # print(x, dx, y, dy)
            self.__ark.clicker.mouse_click(x + dx + 35, y + dy + 13, t=1)
            return True
        while abs(dx) > 669:
            self.__ark.clicker.dragRel(1172, 35, ((-1 if dx > 0 else 1) * 400), 0)
            self.__ark.clicker.mouse_click(510, 35, t=0.2)
            dx += (-1 if dx > 0 else 1) * 660
        while abs(dx) > 172:
            self.__ark.clicker.dragRel(1172, 35, ((-1 if dx > 0 else 1) * 100), 0)
            self.__ark.clicker.mouse_click(510, 35, t=0.2)
            dx += (-1 if dx > 0 else 1) * 172
        while abs(dx) > 70:
            self.__ark.clicker.dragRel(1172, 35, ((-1 if dx > 0 else 1) * 50), 0)
            self.__ark.clicker.mouse_click(510, 35, t=0.2)
            dx += (-1 if dx > 0 else 1) * 70
        # print(x + dx, y + dy)
        reco = self.getMapStageInfo(mapName)
        reco_li = [os.path.basename(i)[:-4] for i, v in reco]
        if stage2 in reco_li:
            cur_x, cur_y = reco[reco_li.index(stage2)][1]
            self.__ark.clicker.mouse_click(cur_x + 35, cur_y + 13, t=1)
            return True
        else:
            logger.warning(f"{stage2} not found in current map")
            self.moveStageInMap(mapName, stage1, stage2)

    def changeStageInMap(self, mapName, stageNameTo, needback=True):
        # 当前状态必须为准备战斗状态(即有开始行动按钮状态)
        if needback and self.__ark.gameTemp.dingwei("on_atk_beg\\start.png",
                                                    self.__ark.getScreenShot(1102, 624, 150, 66)):
            self.__ark.clicker.mouse_click(86, 42, t=1)
        current_can_get_map = [os.path.basename(i)[:-4] for i, v in self.getMapStageInfo(mapName)][0]
        assert self.stageInSameMap(current_can_get_map, stageNameTo, mapName)
        self.moveStageInMap(mapName, current_can_get_map, stageNameTo)

    def fromMaintoMapMain(self):
        self.__ark.clicker.mouse_click(950, 201, t=1.7)

    def toMain(self):
        if self.__ark.getLocation(self.__ark.getScreenShot(), 'main'):
            return True
        if self.__ark.gameTemp.dingwei("main\\main_ref.png", self.__ark.getScreenShot(199, 11, 141, 53)):
            logger.warning('未知识别位置！强制返回主界面并从主界面进行操作，可能会导致异常产生！')
            self.__ark.clicker.mouse_click(269, 39, t=0.7)
            self.__ark.clicker.mouse_click(93, 172, t=2)
            # TODO:检查事件
            self.__ark.check_to_main_notice()
            return True
        return False

    def fromMaptoMapMain(self, mapName: str = None):
        if mapName is None:
            # 自动定位当前位置
            loc = self.__ark.getLocation(self.__ark.getScreenShot(), self.RECO, addon=True)
            logger.debug(f"获得当前定位于{loc}")
            if len(loc) == 0:
                if not self.toMain():
                    logger.error('无法定位当前位置且无法返回主界面！请检查！')
                    # raise ValueError("cannot locate current location")
                    return False
                else:
                    self.__ark.clicker.mouse_click(923, 201, t=1.7)
                    return True
            if loc[0] == 'map_atk':
                # 在攻击界面 但是不知道在哪个关卡的攻击界面
                # 因此还需要返回后再次进行识别
                self.__ark.clicker.mouse_click(86, 42, t=1)
                loc = self.__ark.getLocation(self.__ark.getScreenShot(), self.RECO, addon=True)
                logger.debug("在攻击界面中，返回后执行识别：" + str(loc))
            if not loc:
                if not self.toMain():
                    logger.error("请切换至任一地图、主界面或地图主界面再试一次！")
                    return None
                else:
                    self.__ark.clicker.mouse_click(923, 201, t=1.7)
                    return True
            if loc[0] == 'map_main':
                return True
            if loc[0] == 'main':
                self.__ark.clicker.mouse_click(923, 201, t=1.7)
                return True
            if loc[0] in ['map_ep', 'map_mat', 'map_exterm']:
                if 'map_exterm.inmap' in loc:
                    self.__ark.clicker.mouse_click(86, 42, t=1.5)
                self.__ark.clicker.mouse_click(86, 42, t=1)
                self.__ark.clicker.mouse_click(80, 658, t=1)
                return True
            if loc[0] in ArkMap_ACTIVITY:
                self.__ark.clicker.mouse_click(86, 42, t=1)
                self.__ark.clicker.mouse_click(86, 42, t=1)
                self.__ark.clicker.mouse_click(80, 658, t=1)
                return True
        else:
            # TODO: 存在mapName 进行位置检测
            # 否则需要有开始行动标志的界面介入
            if mapName in ACTIVITY_MAP:
                # 需要额外返回上一级的特殊地图
                self.__ark.clicker.mouse_click(86, 42, t=1.6)

            self.__ark.clicker.mouse_click(86, 42, t=1)
            self.__ark.clicker.mouse_click(86, 42, t=1)
            self.__ark.clicker.mouse_click(80, 658, t=1)
            return True

    def activityMapAdapter(self, oPos, oCond, exPos, exCond, oTime, exTime, beforeTime, targStage, targMap):
        """
        关卡主界面到关卡内部跳转适配
        :param targMap: 目标地图名称
        :param targStage: 目标关卡名称
        :param oPos: 常规图点击坐标
        :param oCond: 常规图点击判别
        :param exPos: EX图点击坐标
        :param exCond: EX图点击判别
        :param oTime: 常规图进入等待时长
        :param exTime: EX图进入等待时长
        :param beforeTime: 处理前延时
        :return: bool
        """
        time.sleep(beforeTime)
        if self.__ark.clicker.mouse_click(*oPos, t=oTime, condition=targStage.startswith(oCond)):
            return True
        elif self.__ark.clicker.mouse_click(*exPos, t=exTime, condition=targStage.startswith(exCond)):
            return True
        else:
            return error_map(targStage, targMap)

    def fromActivityMapMainToActivityMap(self, targMap: str, targStage: str):
        logger.debug(f"Activity MapMain To Map:{targMap} for {targStage}")
        if targMap in ACTIVITY_MAP:
            # TODO:适配所有的活动地图
            time.sleep(1.5)
            if targMap == 'CB':
                return self.activityMapAdapter((1098, 438), 'CB-', (1061, 613), 'CB-EX-', 2, 2, 0, targStage, targMap)
            if targMap == 'MB':
                return self.activityMapAdapter((1140, 162), 'MB-', (1140, 295), 'MB-EX-', 2, 2, 1, targStage, targMap)
            if targMap == 'WR':
                return self.activityMapAdapter((1157, 598), 'WR-', (1030, 630),
                                               'WR-EX-', 1.7, 1.7, 1.7, targStage, targMap)
            if targMap == 'OD':
                return self.activityMapAdapter((205, 317), 'OD-', (205, 397), 'OD-EX-', 2, 2, 1.5, targStage, targMap)
            if targMap == 'DM':
                return self.activityMapAdapter((789, 523), 'DM-', (870, 640), 'DM-EX-', 1.3, 1.5, 1.5, targStage, targMap)

            logger.error(f"当前地图'{targMap}'尚未适配进入模式，请在ArkMap中进行适配后再次运行")
            return False
        return True

    def fromMapMainToMap(self, mapName: str):
        if mapName[0:2] == 'EP':
            map_id = int(mapName[2:])
            tab_id, pos = self.checkMapClose(map_id)
            self.__ark.clicker.mouse_click(pos[0], pos[1], t=1.8)
            self.changeMapEP(map_id, tab_id)
            return True
        if mapName in NORMAL_MAP:
            self.__ark.clicker.mouse_click(239, 657, t=0.5)
            ret = self.__ark.gameTemp.dingwei(f"main\\map\\i_{mapName}.png",
                                              self.__ark.getScreenShot(0, 348, 1280, 44), 0.94)
            if not ret:
                logger.error(f"未找到地图{mapName}")
                return False
            x, y = ret[0]
            x += 15
            y += 348 - 60
            self.__ark.clicker.mouse_click(x, y, t=1.7)
            return True
        if mapName in ACTIVITY_MAP:
            # log inrange 774,621,495,59
            resl = self.__ark.gameTemp.dingwei("main\\map\\a_" + mapName + ".png",
                                               self.__ark.getScreenShot(774, 621, 495, 59), threshold=0.82)
            if resl:
                x, y = resl[0]
                self.__ark.clicker.mouse_click(x + 774 + 52, y + 621 + 15, t=0.7)
                return True
            else:
                logger.error(f"未找到当前定位的活动地图‘{mapName}’,请确认当前活动地图已开放")
                return False
        logger.error(f"地图{mapName}不存在！")
        return False

    def changeStage(self, currentStageName, targetStageName, currentMapName=None, targetMapName=None):
        currentMapName = self.getStageInfo(currentStageName)[0] if currentMapName is None else currentMapName
        targetMapName = self.getStageInfo(targetStageName)[0] if targetMapName is None else targetMapName
        if currentMapName != targetMapName:
            logger.debug(f"从{currentMapName}到主页")
            if not self.fromMaptoMapMain(currentMapName):
                logger.error("出现错误，停止。请检查")
                return False
            logger.debug(f"从主页到{targetMapName}")
            assert self.fromMapMainToMap(targetMapName)
            assert self.fromActivityMapMainToActivityMap(targetMapName, targetStageName)
        self.changeStageInMap(targetMapName, targetStageName)
        return True

    def changeMapEP(self, target: int, current: int = -1):
        if current == -1:
            current = getCurrentEpisode(self.__ark)
        if current == target:
            return True
        if target > current:
            x, y = (1186, 666)
        else:
            x, y = (983, 666)
        for _ in range(abs(current - target)):
            self.__ark.clicker.mouse_click(x, y, t=2)

    def _map_template(self, name):
        return {"name": name,
                "root": "",
                "stages": []}

    def _createMap(self, name: str = "EP0"):
        assert name not in self.root["maps"]
        assert name != 'root'
        self.root["maps"].append(name)
        self.maps.update({name: self._map_template(name)})
        logger.notice(f"完成{name}的创建！")

    def _setBaseStage(self, name: str, stage: str):
        assert name in self.root["maps"]
        self.maps[name]["root"] = stage
        self.maps[name]["stages"].append([stage, (0, 0)])
        logger.notice(f"设定{name}原点关卡为{stage}")

    def _addStageInMap(self, mapName: str, stageName: str, x: int, y: int):
        self.maps[mapName]["stages"].append([stageName, (x, y)])

    def _autoDetect(self, name: str, overwrite=False):
        assert name in self.root["maps"], f"不存在地图{name}"
        root_stage = self.maps[name]["root"]
        assert root_stage != '', f"地图{name}中无数据！请先设置地图根节点"
        apd_stage = []
        basex, basey = 0, 0
        # rect_stage = [os.path.basename(i)[:-4] for i, v in rect]
        rect = self.getMapStageInfo(name)
        rect_stage = [os.path.basename(i)[:-4] for i, v in rect]
        logger.debug(rect_stage)
        for stage, where in self.maps[name]["stages"]:
            if stage in rect_stage:
                apd_stage = [stage, where]
                basex, basey = rect[rect_stage.index(stage)][1]
                logger.debug(f"寻找到已知根节点{apd_stage}位于{basex},{basey},退出循环")
                break
        assert apd_stage != [], f"在地图中未寻找到已知节点！"

        dx, dy = apd_stage[1]
        dx -= basex
        dy -= basey
        _exist_stage = [i for i, v in self.maps[name]["stages"]]
        for stage, where in rect:
            real_stage = os.path.basename(stage)[:-4]
            if (real_stage != apd_stage[0] and real_stage not in _exist_stage) or overwrite:
                self._addStageInMap(name, real_stage, int(dx + where[0]), int(dy + where[1]))
                logger.notice(f"add {real_stage} in {name} at {dx + where[0]},{dy + where[1]}")
        return True

    def _removeMap(self, name: str = "EP0"):
        assert name in self.root["maps"]
        self.root["maps"].remove(name)
        self.maps.pop(name)

    def _writeSetting(self):
        with open(self._data_path, 'w', encoding='utf-8') as f:
            json.dump(self.root, f)
        fold = os.path.dirname(self._data_path) + '\\'
        for v in self.maps.keys():
            with open(fold + v + ".json", 'w', encoding="utf-8") as f:
                json.dump(self.maps.get(v), f)

    def _catchNewMap(self, name, base=0):
        # map as 100x36
        scrshot = self.__ark.getScreenShot(790 + base * 153, 635, 100, 36)
        import cv2
        cv2.imwrite(f"./imgReco/img/main/map/a_{name}.png", scrshot)
        return True
# USAGE: from ArkMapping.ArkMap import ArkMap;a = ArkMap(ark_main)
#        a._catchNewMap("BH")
#        mapSave(True,"BH")
#        a._createMap("EP5");a._setBaseStage("EP5","5-1") -> a._autoDetect("EP5") * N -> a._writeSetting()
#        <ADD CODE> Static.py -> ACTIVITY_MAP;ArkMap_RECO;ArkMap_ACTIVITY
#        ## APPEND FOR MAP-COND
#        ark.mapper.addMap('map_OD') -> ark.mapper.addLocate_Auto('map_OD','main\\activity\\OD_atk.png',getscreenshot())
#        <ADD CODE> ArkMap.py fromActivityMapMainToActivityMap()
