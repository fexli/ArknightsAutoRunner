import os
import time
import json
from utils.utils import PushableDict
from utils.logger import root_logger as logger
from ArkTagData.TagGetter import getGameTempGlobal
import numpy as np
from utils.logger import color
from functools import singledispatch
import cv2


def _check_type_num(dt, type_):
    r = 0
    for _ in dt:
        if _["type"] == type_:
            r += 1
    return r


class Detectors(list):
    MAX_DISTANCE = np.linalg.norm(np.array([255, 255, 255]))
    CONDITION_KEY = {"%image_num%": lambda det, res, suc: _check_type_num(det, 'I'),
                     "%color_num%": lambda det, res, suc: _check_type_num(det, 'C'),
                     "%image_suc%": lambda det, res, suc: suc[0],
                     "%color_suc%": lambda det, res, suc: suc[1]}
    CONDItiON_DEFAULT = '%image_suc% >= %image_num% - 1 and %color_suc% >= %color_num% - 2'

    def __init__(self, li=None):
        super(Detectors, self).__init__(li) if li else super(Detectors, self).__init__()
        self.__gameTemp__ = getGameTempGlobal()

    def _auto_detect(self, dobj, image, sub_area=None):
        if dobj['type'] == 'C':
            return self._detect_color(dobj, image, sub_area=sub_area)
        if dobj["type"] == 'I':
            return self._detect_image(dobj, image, sub_area=sub_area)
        return None

    def _get_distance(self, d1, d2, sub_area=None):
        # logger.debug(f"_GET DIST [{d1}] and [{d2}] with {np.linalg.norm(d1 - d2)} / {self.MAX_DISTANCE}")
        return np.linalg.norm(d1 - d2) / self.MAX_DISTANCE

    def _detect_image(self, dobj, image, sub_area=None):
        # {"type": type_,
        #  "image": imagePath,
        #  "threshold": threshold,
        #  "area": list(locationarea) if locationarea else None,
        #  "diff": diff}
        #  read with x,y,w,h dump x1,x2,y1,y2
        if sub_area is None:
            if dobj["area"] is not None:
                x, y, w, h = dobj["area"]
                img = image[y:y + h, x:x + w]
            else:
                img = image
        else:
            img = image
            if (sub_area[0] > dobj["area"][0] and sub_area[1] > dobj["area"][1]) or \
                    (sub_area[2] < dobj["area"][2] and sub_area[3] < dobj["area"][3]):
                return 'I', dobj["diff"], 0, True

        try:
            result = np.max(
                self.__gameTemp__.matchDifference(img, self.__gameTemp__.getTemplate(dobj["image"])[0], method=2))
        except ValueError:
            logger.error(f"Image load failed:{dobj['image']}")
            result = 0
        except cv2.error:
            logger.error(f"Image compare failed:{dobj['image']}")
            result = 0
        return 'I', dobj["diff"], 0 if result > dobj["threshold"] else 1, False

    def _detect_color(self, dobj, image, sub_area=None):
        x, y = dobj["pos"]
        r, g, b = dobj["color"]
        if sub_area is None:
            return 'C', dobj["diff"], self._get_distance(np.array((b, g, r)), image[y - 1][x - 1]), False
        if sub_area[0] < x < sub_area[0] + sub_area[2] and sub_area[1] < y < sub_area[1] + sub_area[3]:
            return 'C', dobj["diff"], self._get_distance(np.array((b, g, r)),
                                                         image[y - sub_area[1] - 1][x - sub_area[0] - 1]), False
        return 'C', dobj["diff"], 0, True

    def _replace_condition_value(self, condition: str, res, suc, show=False):
        for i, rp in self.CONDITION_KEY.items():
            condition = condition.replace(i, str(rp(self, res, suc)))
        # TODO:{l[0]}.format(l=list)
        if show:
            logger.debug("condition:" + condition)
        return condition

    def _detect_condition(self, result, condition, suc, show):
        _cond = self._replace_condition_value(condition, result, suc, show)
        if _cond == '':
            return True
        try:
            return bool(eval(_cond))
        except Exception as e:
            logger.error(f"Detect ERROR!(cond='{_cond}'):{e}")
            return None

    def detect(self, image, condition, sub_area=None, type='L', show=False):
        result = []
        suc = {'I': 0, 'C': 0}
        for dobj in self:
            ret = self._auto_detect(dobj, image, sub_area=sub_area)
            if ret is None:
                logger.error("Wrong type of detector!%s" % dobj.get("type"))
                continue
            suc[ret[0]] += (1 if ret[2] < 0.2 else 0)
            result.append(ret)
        return result, self._detect_condition(result, condition, [suc['I'], suc['C']], show)

    def addDetector(self, type_="I",  # 类型 暂时有I(image) C(color)
                    imagePath=None,  # I>定位图像位置>GameTemplate.dingwei
                    threshold=None,  # I>定位图像精度
                    locationarea=None,  # I>定位区域(截图区域)
                    pos=None,  # C>颜色对应的位置
                    color=None,  # 颜色值
                    diff=None):  # 重要程度
        if type_ == 'I':
            self.append({"type": type_,
                         "image": imagePath,
                         "threshold": threshold,
                         "area": list(locationarea) if locationarea else None,
                         "diff": diff})
        elif type_ == "C":
            self.append({"type": type_,
                         "pos": list(pos),
                         "color": list(color),
                         "diff": diff})

    def delDetector_Index(self, i):
        return self.pop(i)

    def delDetector_XY(self, x, y):
        pass


class Addon(dict):
    def __init__(self, addon=None):
        if addon is None:
            super(Addon, self).__init__()
        else:
            super(Addon, self).__init__({addon_key: {"detector": Detectors(addon.get(addon_key).get("detector")),
                                                     "condition": addon.get(addon_key)
                                        .get("condition", Detectors.CONDItiON_DEFAULT)} for addon_key in addon.keys()})

    def addAddon(self, name, condition=None):
        if self.get(name, None) is None:
            self.update({name: {"detector": Detectors(None),
                                "condition": condition or Detectors.CONDItiON_DEFAULT}})

    def hasAddon(self, name):
        return name in self.keys()


class Mapping(object):
    LOCATE_RAW = 0
    LOCATE_MIN = 1
    LOCATE_MIN_RELATE = 2
    LOCATE_CONDITION = 3

    def __init__(self, path: str = ''):
        self.path = path
        self.mapping = PushableDict(self._loadMapping(path))
        self.__gameTemp__ = getGameTempGlobal()

    def _loadMapping(self, path):
        if not os.path.isfile(path):
            return {"map": PushableDict(), "reflector": PushableDict().set_base(list)}
        with open(path, 'r', encoding="utf-8") as f:
            mapping = json.load(f)
        map_ = PushableDict().set_base(dict)
        reflect_ = PushableDict(mapping.get("reflector", {})).set_base(list)
        group_ = PushableDict(mapping.get("group", {})).set_base(list)
        mapping = mapping.get("map", {})
        for _key in mapping.keys():
            map_data = mapping.get(_key)
            map_.update({_key: {"detector": Detectors(map_data.get("detector", [])),
                                "addon": Addon(map_data.get("addon", {})),
                                "condition": map_data.get("condition", Detectors.CONDItiON_DEFAULT)}})
        return {"map": map_,
                "reflector": reflect_,
                "group": group_}

    def writeMapping(self, path=None):
        if path is not None:
            self.path = path
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.mapping, f)
        return True

    def _default_map_template(self, name, detector=None, addon=None, condition=None):
        return {name: {"detector": Detectors(detector),
                       "addon": Addon(addon),
                       "condition": Detectors.CONDItiON_DEFAULT if condition is None else str(condition)}}

    def setCondition(self, name, condition):
        assert self.checkMapExist(name)
        self.mapping.get("map").get(name)["condition"] = str(condition)

    def hasMap(self, name):
        return name.split('.')[0] in self.mapping.get("map").keys()

    def getMap(self, name):
        if '.' in name:
            base_name, addon_name = name.split('.', 1)
            if not self.mapping.get('map').get(base_name)['addon'].hasAddon(addon_name):
                self.mapping.get('map').get(base_name)['addon'].addAddon(addon_name)
            return self.mapping.get('map').get(base_name)['addon'].get(addon_name)
        else:
            return self.mapping.get("map").get(name)

    def addMap(self, name, condition=None):
        if '.' in name:
            name_bef, name_after = name.split('.', 1)
            if not self.mapping.get('map').has(name_bef):
                logger.warning(name + " doesn't in the MapList")
                return False
            self.mapping.get('map').get(name_bef).get('addon').addAddon(name_after)
        else:
            if self.mapping.get("map").has(name):
                logger.warning(name + " has already in the MapList")
                return False
            self.mapping.get("map").update(self._default_map_template(name, condition=condition))
            self.mapping.get("reflector").push(name, name, create=True)
        return True

    def delMap(self, name):
        assert self.checkMapExist(name)
        self.mapping.get("reflector").pop(name)
        return self.mapping.get("map").pop(name)

    def checkMapExist(self, name):
        if not self.hasMap(name.split('.', 1)[0]):
            logger.warning("不存在名为" + name.split('.', 1)[0] + "的Map")
            return False
        return True

    def hasGroup(self, name):
        return name in self.mapping.get("group").keys()

    def createGroup(self, name):
        assert not self.hasGroup(name)
        self.mapping.get("group").new(name)

    def addGroupMap(self, name, *mapname):
        for mname in mapname:
            self.mapping.get("group").push(name, mname, create=True)

    def addPoint(self, name, image, x, y, diff=1):
        assert self.checkMapExist(name)
        b, g, r = image[y - 1][x - 1]
        self.getMap(name).get("detector").addDetector(type_='C', pos=[x, y], color=[int(r), int(g), int(b)], diff=diff)
        return True

    def addPoints(self, name, image, diff=1, *xy):
        for x, y in xy:
            self.addPoint(name, image, x, y, diff)
        return True

    def delPoint(self, name, index=None, x=None, y=None):
        assert self.checkMapExist(name)
        _detector = self.getMap(name).get("detector")
        if index is not None:
            _detector.delDetector_Index(index)
        elif x is not None and y is not None:
            _detector.delDetector_XY(x, y)
        else:
            logger.error("index and (x,y) can not be None at sametime")
            return False
        return True

    def addLocate_withPath(self, name, imagePath, threshold=0.96, area=None, diff=5):
        assert self.checkMapExist(name)
        # save as x,y,w,h
        self.getMap(name).get("detector").addDetector(type_='I', imagePath=imagePath, threshold=threshold,
                                                      locationarea=area, diff=diff)
        return True

    def addLocate_Auto(self, name, imagePath, image, area=None, threshold=0.95, diff=5):
        assert self.checkMapExist(name), '地图不存在！'
        assert self.__gameTemp__.has(imagePath), '图片不存在！'
        template = self.__gameTemp__.getTemplate(imagePath)[0]
        max_thres, where = self.__gameTemp__.matchDifference(image, template, method=1)
        logger.debug("在(%d,%d)匹配到%s的最佳阈值%s" % (where[0], where[1], imagePath, max_thres))
        if max_thres < threshold:
            logger.error("未找到最为匹配的源，请尝降低变最高阈值")
            return False
        y, x = int(where[0]), int(where[1])
        h, w, depth = template.shape
        area = [x - 2, y - 2, w + 4, h + 4] if area is None else area
        self.getMap(name).get("detector") \
            .addDetector(type_='I', imagePath=imagePath, threshold=max_thres - 0.07, locationarea=area, diff=diff)
        logger.notice(
            "成功在%s中添加关键图像%s[area=[%d,%d,%d,%d],threshold=%.2f]" % (name, imagePath, x, y, w, h, max_thres - 0.07))
        return True

    def testCondition(self, name, image, sub_area=None):
        assert self.hasMap(name), '地图不存在！'
        condition = self.getMap(name).get("condition")
        logger.debug("current condition(of %s) is %s" % (name, condition))
        detector = self.getMap(name).get("detector")
        ret, pass_ = detector.detect(image, condition, sub_area=sub_area)
        logger.debug("==================Detail==================")
        index = 0
        for t, diff, val, skip in ret:
            if skip:
                msg = color.print.BLUE + "[SKIP]" + color.print.END
            else:
                msg = color.print.DARKGREEN + "[PASS]" + color.print.END if val < 0.2 else \
                    color.print.RED + "[FAIL]" + color.print.END
            msg += color.print.CYAN + t.replace("I", "[IMAGE]").replace("C", "[COLOR]") + color.print.END
            if t == 'C':
                msg += f"POS{str(detector[index]['pos'])},VALUE={val}"
            elif t == 'I':
                msg += f'[{detector[index]["image"]},thr={round(detector[index]["threshold"], 2)}]'
            msg += ',diff=%.1f' % diff
            logger.debug(msg)
            index += 1
        logger.debug(color.print.GREEN + "condition pass through" + color.print.END) \
            if pass_ else logger.debug(color.print.RED + "condition failed" + color.print.END)
        logger.debug("==================Detail==================")

    def locateImage(self, image, ranges=None, group=None, method=3, sub_area=None, addon=False, show_debug=False):
        _s = time.time()
        if group is not None:
            assert self.hasGroup(group)
            ranges = self.mapping.get("group").get(group)
        else:
            if isinstance(ranges, str):
                ranges = [ranges]
            ranges = ranges if ranges is not None else self.mapping.get("reflector").keys()

        result = {}
        for _ in ranges:
            result.update({_: self.mapping.get("map").get(_).get("detector")
                          .detect(image, self.mapping.get("map").get(_).get('condition', ''),
                                  sub_area=sub_area, show=show_debug)})
        if show_debug:
            logger.debug('Solve locating in %.3f secs' % (time.time() - _s))
        if method == 3:
            ret = []
            for name, v in result.items():
                if v[1] is True:
                    ret.append(name)
            # parse addon
            if not addon:
                return ret

            ret2 = ret.copy()
            for mapname in ret:
                for addon_name, v in self.getMap(mapname).get('addon').items():
                    nil, suc = v.get('detector').detect(image, v['condition'], sub_area=sub_area, show=show_debug)
                    if suc:
                        ret2.append(f"{mapname}.{addon_name}")
            return ret2
        elif method == 0:
            return result
        elif method == 1:
            return {_: sum([i * k for n, i, k in result.get(_)[0]]) for _ in result}
        elif method == 2:
            return {_: sum([i * k for n, i, k in result.get(_)[0]]) / sum([i for n, i, k in result.get(_)[0]])
                    for _ in result}

        raise ValueError("unknown method for locateImage()")
