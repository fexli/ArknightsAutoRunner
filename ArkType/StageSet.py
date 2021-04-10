from utils.logger import root_logger as logger


class Stage(dict):
    def __init__(self, stageName, max_atk, require=None, use_require=False):
        super(Stage, self).__init__({"stage": stageName,
                                     "max_atk": max_atk,
                                     "require": require,
                                     "use_require": use_require})

    def __truediv__(self, other):
        if isinstance(other, (float, int)):
            self.update({"max_atk": int(self.get("max_atk") / other)})
        else:
            raise ValueError(f'other must be a number not "{other.__class__.__name__}"')


class StageSet(dict):
    def __init__(self, total_max_atk=-1, use_ap_supply=True, use_diamond=False):
        _MT = {"stages": [],  # 要攻击的关卡信息
               "list": [],  # 要攻击的关卡列表
               "use_ap_supply": use_ap_supply,
               "use_diamond": use_diamond,
               "total_max_atk": total_max_atk,
               }
        super(StageSet, self).__init__(_MT)

    def __truediv__(self, other):
        _li: list = self.get('list')
        for stage in self.get("stages"):
            stage /= other
        self.removeZeroAtkStage()

    def removeZeroAtkStage(self):
        li = self.get("list")
        li_c = li.copy()
        li_c.reverse()
        stages = self.get("stages")
        len_ = len(li_c)
        for i, v in enumerate(li_c):
            if stages[len_ - i - 1].get("max_atk") == 0:
                stages.pop(len_ - i - 1)
                li.pop(len_ - i - 1)

    def use_ap_supply(self, bo=True):
        self['use_ap_supply'] = bo
        return self

    def use_diamond(self, bo=True):
        self['use_diamond'] = bo
        return self

    def set_total_max_atk(self, max_atk=-1):
        self["total_max_atk"] = max_atk

    @staticmethod
    def readFromFile(path):
        pass

    @staticmethod
    def fromPlanner(planned_data, require_request=False):
        if not isinstance(planned_data, dict):
            logger.error(f"规划数据并非dict形式，请检查(获得了{planned_data.__class__.__name__})")
            return StageSet()
        stages = planned_data.get("stages", [])
        if not stages:
            logger.warning("规划数据关卡列表为空！")
            return StageSet()
        ret = StageSet()
        for stage in stages:
            ret.addStage(stage['stage'], int(float(stage['count']) + 0.9), stage['items'], require_request)
        return ret

    def getCost(self):
        from ArkTagData.TagGetter import getMapCost
        map_cost = getMapCost()
        cost = [0, 0]
        _INF = [False, False]
        for _ in self['stages']:
            _COTYPE, _COST = map_cost.where(_['stage']).split('_')
            _COTYPE = [0, 1][['ap', 'et'].index(_COTYPE)]
            _COST = int(_COST) * _['max_atk']
            if _['max_atk'] == -1:
                _INF[_COTYPE] = True
            cost[_COTYPE] += _COST
        logger.debug(f"共计消耗{cost[0] if _INF[0] is False else 'INFINITE'}理智,"
                     f"{cost[1] if _INF[1] is False else 'INFINITE'}门票")
        return cost

    def addStage(self, stageName, times, require=None, append=False):
        if stageName in self['list']:
            if append is self:
                logger.warning(f"已存在名为{stageName}的关卡在攻击列表中,若需要添加请使用append=True更新攻击次数")
                return self
            else:
                self['stages'][self['list'].index(stageName)]["max_atk"] += times
                return self
        self["list"].append(stageName)
        self['stages'].append(Stage(stageName, times, require))
        return self

    def delStage(self, stageName, times):
        if stageName not in self["list"]:
            return self
        max_atk = self["stages"][self["list"].index(stageName)]["max_atk"]
        if max_atk - times <= 0:
            logger.debug(f"删除Stage:{stageName}")
            _INDEX = self["list"].index(stageName)
            self["stages"].pop(_INDEX)
            self["list"].pop(_INDEX)
        else:
            self["stages"][self["list"].index(stageName)]["max_atk"] -= times
        return self
