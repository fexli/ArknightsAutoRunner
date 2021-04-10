import json
import time
import os

from utils.DictUtil import ItemDict
from utils.utils import PushableDict
from config.RootData import RootData
from ArkGameData.TagDefine import AkaRecruitDefine
from ArkType.Character import CharacterDict
from ArkType.StageExcel import StageExcel


def getRecruitFirstChar() -> list:
    pass


@RootData.cache("recruit_tag")
def getRecruitTag() -> dict:
    with open("./ArkGameData/RecruitData.json", "r", encoding='utf-8') as f:
        ret = json.load(f)
    return ret


@RootData.cache("recruit_aka_tag")
def getRecruitAkaTag() -> PushableDict:
    recruit_aka = AkaRecruitDefine
    return recruit_aka


@RootData.cache("char_tag")
def getCharTag() -> CharacterDict:
    char_json_path = os.path.join(".\\ArknightsGameData\\zh_CN\\gamedata\\excel\\character_table.json")
    with open(char_json_path, 'r', encoding="utf-8") as f:
        char_data = CharacterDict(json.load(f))
    return char_data


@RootData.cache("char_rate_tag")
def getCharRateTag() -> PushableDict:
    chars = getCharTag()
    rarityTable = PushableDict([1, 2, 3, 4, 5, 6], base=list)
    for _ in chars:
        char = chars.get(_)
        rarityTable.push(char.get("rarity") + 1, char.get("name"))
    return rarityTable


@RootData.cache("item_tag")
def getItemTag() -> ItemDict:
    # if RootData.has("item_tag"):
    #     return RootData.get("item_tag")
    item_json_path = os.path.join("ArknightsGameData", "zh_CN", "gamedata", "excel", "item_table.json")
    with open(item_json_path, 'r', encoding="utf-8") as f:
        item_data = json.load(f)
    # RootData.set("item_tag", item_data)
    return ItemDict(item_data)


@RootData.cache("item_name_list")
def getItemNameList() -> list:
    item_json_path = os.path.join(".\\ArknightsGameData\\zh_CN\\gamedata\\excel\\item_table.json")
    with open(item_json_path, 'r', encoding="utf-8") as f:
        item_data = json.load(f)
    name_list = []
    for i, _ in item_data["items"].items():
        name_list.append(_["name"])
    return name_list


@RootData.cache("stage_tag")
def getStageTag() -> StageExcel:
    stage_json_path = ".\\ArknightsGameData\\zh_CN\\gamedata\\excel\\stage_table.json"
    with open(stage_json_path, 'r', encoding="utf-8") as f:
        stage_json = json.load(f)
    return StageExcel(stage_json)


@RootData.cache("GameTempGlobal")
def getGameTempGlobal():
    from imgReco.gameTemplate import GameTemplate
    return GameTemplate("./imgReco/img/")


@RootData.cache('ActivityOpen', max_cache_time=86400)
def getActivityOpen():
    activity_table = getRawExcelJsonData("activity_table")
    open_stage_id_li = [v["id"] for k, v in activity_table["basicInfo"].items() if
                        v.get("rewardEndTime", 0) > time.time()]
    ministory_drop_li = [v["tokenItemId"] for k, v in activity_table["activity"]["MINISTORY"].items() if
                         k in open_stage_id_li]
    return open_stage_id_li, ministory_drop_li


def getRawExcelJsonData(jsonNameWithOutJsonSuffix: str):
    if not os.path.exists(f".\\ArknightsGameData\\zh_CN\\gamedata\\excel\\{jsonNameWithOutJsonSuffix}.json"):
        raise ValueError(f"No json named '{jsonNameWithOutJsonSuffix}.json' in excel folder")

    @RootData.cache(f"raw_{jsonNameWithOutJsonSuffix}")
    def getRawExcelJsonDataInner(name):
        json_path = os.path.join(f".\\ArknightsGameData\\zh_CN\\gamedata\\excel\\{name}.json")
        with open(json_path, 'r', encoding="utf-8") as f:
            data = json.load(f)
        return data

    return getRawExcelJsonDataInner(jsonNameWithOutJsonSuffix)


def getDropList(stageCode):
    stages = getStageTag()["stages"]
    items = getItemTag()["items"]
    stage_data = [stages[i] for i in stages.keys() if stages[i]['code'] == stageCode and "#f#" not in stages[i]][0]
    # return stage_data
    drop_list = {(items[i["id"]]["iconId"], items[i["id"]]["name"]) for i in
                 stage_data["stageDropInfo"]["displayDetailRewards"] if
                 i["type"] != "CHAR" and items.get(i["id"]) is not None}  # 过滤掉家具和角色
    drop_list.add(("GOLD", "龙门币"))
    drop_list.add(("EXP_PLAYER", "声望"))
    return drop_list

@RootData.cache("building_data")
def getBuildingData():
    building_json_path = ".\\ArknightsGameData\\zh_CN\\gamedata\\excel\\building_data.json"
    with open(building_json_path, 'r', encoding="utf-8") as f:
        building_json = json.load(f)
    return building_json


@RootData.cache("shop_client_table")
def getShopClient():
    shop_client_path = ".\\ArknightsGameData\\zh_CN\\gamedata\\excel\\shop_client_table.json"
    with open(shop_client_path, 'r', encoding="utf-8") as f:
        shop_table = json.load(f)
    return shop_table


def getActivity():
    return getRawExcelJsonData("activity_table")


@RootData.cache('map_cost_define')
def getMapCost() -> PushableDict:
    map_cost_path = os.path.join(".\\ArknightsGameData\\zh_CN\\gamedata\\excel\\stage_table.json")
    with open(map_cost_path, 'r', encoding="utf-8") as f:
        stage_table = json.load(f)
    map_cost_define = PushableDict([], base=list)
    for stage in stage_table["stages"]:
        if "#f#" not in stage:
            stageData = stage_table["stages"].get(stage)
            code = stageData.get("code")
            apC = stageData.get("apCost")
            etC = stageData.get("etCost")
            if etC > 0:
                map_cost_define.push("et_%d" % etC, code, create=True)
            else:
                map_cost_define.push("ap_%d" % apC, code, create=True)
    return map_cost_define


@RootData.cache('rogue_like_items')
def getRogueLikeItems() -> dict:
    rogue_json_path = os.path.join(".\\ArknightsGameData\\zh_CN\\gamedata\\excel\\roguelike_table.json")
    with open(rogue_json_path, 'r', encoding="utf-8") as f:
        rogue_data = json.load(f)
    return rogue_data['itemTable']["items"]


@RootData.cache('rogue_like_item_name_dict')
def getRogueLikeItemNameDict() -> dict:
    name_list = {}
    for name, _ in getRogueLikeItems().items():
        name_list.update({name: _["name"]})
    return name_list


def getCharNameDict() -> dict:
    nl = {}
    for name, val in getCharTag().items():
        nl.update({name: val['name']})
    return nl


@RootData.cache('skin_table')
def getSkinTable() -> dict:
    skin_table_path = os.path.join(".\\ArknightsGameData\\zh_CN\\gamedata\\excel\\skin_table.json")
    with open(skin_table_path, 'r', encoding="utf-8") as f:
        skin_data = json.load(f)
    return skin_data['charSkins']


@RootData.cache('skin_name_dict')
def getSkinNameDict() -> dict:
    nl = {}
    chars = getCharTag()
    for name, v in getSkinTable().items():
        if (skinName := v['displaySkin'].get('skinName')) is not None:
            skinName = f"#{skinName}"
        else:
            skinName = ''
        if (skinGroupName := v['displaySkin'].get('skinGroupName')) is not None:
            skinGroupName = f"({skinGroupName})"
        else:
            skinGroupName = ''
        buildSkinName = f"{chars[v['charId']]['name']}{skinName}{skinGroupName}"
        nl.update({name: buildSkinName})
    return nl


def getItemNameDict() -> dict:
    nl = {}
    for i, _ in getItemTag()["items"].items():
        nl.update({i: _["name"]})
    return nl


def getFurniItemNameDict() -> dict:
    nl = {}
    for i, _ in getBuildingData()['customData']['furnitures'].items():
        nl.update({i: _['name']})
    return nl
