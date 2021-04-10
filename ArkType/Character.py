from utils.logger import root_logger as logger
from rich.table import Table


class AttackRange:
    # Ranges-code ((height,width),[(dx,dy,type)...],shows_str)
    # Ranges-type 0=self 1=atk 2=empty(deleted)
    # RANGES = {
    #     '3-16': ((1, 4), [(3, 0, 1)], ['0221']),
    #  http://prts.wiki/w/%E6%94%BB%E5%87%BB%E8%8C%83%E5%9B%B4%E4%B8%80%E8%A7%88
    # }

    def __init__(self, code):
        self.code = code


class Character(dict):
    def __init__(self, raw):
        super(Character, self).__init__(raw)

    def getSkillUpgradeCost(self, skillID=0, level_from=1, level_to=7, show=False):
        from ArkType.ItemStack import ItemStack
        skillID -= 1
        if len(self["skills"]) < skillID:
            logger.error(f"该角色无第{skillID}技能 最大技能:{len(self['skills'])}")
            return ItemStack()
        ret = ItemStack()
        for level in range(level_from, level_to):
            try:
                if level <= 6:
                    for item in self["allSkillLvlup"][level - 1]['lvlUpCost']:
                        ret.addItemFromCharCost(item)
                elif 6 < level <= 9:
                    for item in self["skills"][skillID]["levelUpCostCond"][level - 7]["levelUpCost"]:
                        ret.addItemFromCharCost(item)
            except Exception as e:
                logger.error(f"CHAR={self['name']},SKILL={skillID},LVL={level},ERR={str(e)}")
        if show:
            logger.notice(f"{self['name']}{skillID}技能 {level_from}->{level_to} "
                          f"消耗{ret.formatItems('%item%(%quantity%) ')}")
        return ret

    def getEvolveCost(self, now=1, target=2):
        from ArkType.ItemStack import ItemStack
        if target < now:
            logger.error(f"角色目标精英化阶段需要大于当前精英化阶段")
            return ItemStack()
        ret = ItemStack()
        for targ in range(now, target):
            _UM = targ + 1
            try:
                for item in self["phases"][_UM]["evolveCost"]:
                    ret.addItemFromCharCost(item)
            except Exception as e:
                logger.error(f"CHAR={self['name']},EVOLVE={_UM},ERR={str(e)}")
        return ret


class CharacterDict(dict):
    def __init__(self, raw: dict):
        super(CharacterDict, self).__init__()
        for name, data in raw.items():
            self.update({name: Character(data)})

    def get(self, arg):
        _GET = super(CharacterDict, self).get(arg, None)
        if _GET is not None:
            return _GET
        for k, v in self.items():
            if v["name"] == arg:
                return v
        return None
