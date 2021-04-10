import json
from ArkGameData import TagDefine
from utils.utils import PushableDict
from utils.logger import root_logger as logger
from .TagGetter import getCharTag
import os


def updateRecruitTag(path="./ArknightsGameData"):
    try:
        char_data = getCharTag()
        obtain_char = PushableDict(TagDefine.ObtainDefine, base=list)
        for _ in char_data:
            char = char_data.get(_)
            c_name = char.get("name")
            if c_name in TagDefine.RecruitCharDefine:
                # 先处理tagList
                c_tag = char.get("tagList")
                c_tag = [] if c_tag is None else c_tag
                for tag in c_tag:
                    obtain_char.push(tag, c_name)
                # 然后是稀有度(1星->支援机械)
                c_rarity = int(char.get("rarity", -1)) + 1
                if c_rarity == 1:
                    obtain_char.push("支援机械", c_name)
                elif c_rarity == 5:
                    obtain_char.push("资深干员", c_name)
                elif c_rarity == 6:
                    obtain_char.push("高级资深干员", c_name)
                # 然后是职业
                c_prof = char.get("profession", "NONE")
                obtain_char.push(getattr(TagDefine.ProfDefine, c_prof), c_name)
                # 最后处理近战位和远程位
                obtain_char.push(getattr(TagDefine.ProfDefine, char.get("position")), c_name)
        # 费用回复建立在先锋干员之上，排除夜刀
        for _ in obtain_char.get("先锋干员"):
            if _ != "夜刀":
                obtain_char.push("费用回复", _)
        with open("./ArkGameData/RecruitData.json", "w", encoding="utf-8") as f:
            json.dump(obtain_char, f, ensure_ascii=False)
        return True
    except:
        return False


def updateItemData():
    import requests
    from bs4 import BeautifulSoup as soup
    k = requests.get("http://prts.wiki/w/%E9%81%93%E5%85%B7%E4%B8%80%E8%A7%88")
    r = soup(k.content, "html.parser")
    item_dump = []
    for data in list(r.find_all(class_="smwdata")):
        item_dump.append([data.get("data-name"), data.get("data-rarity"), data.get("data-file"), data.get("data-id")])
    with open(".\\ArknightsGameData\\zh_CN\\gamedata\\excel\\item_table.json", "r", encoding="utf-8") as f:
        item = json.load(f)
    item_from_json = item["items"]
    item_names = {item_from_json.get(i)["name"]: item_from_json.get(i)["iconId"] for i in item_from_json.keys()}

    # for name, _, __, ___ in item_dump:
    #     try:
    #         item_names.remove(name)
    #     except ValueError:
    #         print(name)
    # print(item_names)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
    }
    patch_item_name_data = {
        "合约赏金（旧）": "CRISIS_SHOP_COIN",
        "晶体电子单元": "MTL_SL_OEU",
        "寻访数据契约（遗愿焰火）": "LMTGS_COIN_601",
        "寻访数据契约（勿忘我）": "LMTGS_COIN_903",
        "寻访数据契约（地生五金）": "LMTGS_COIN_1401",
        "寻访数据契约（月隐晦明）": "LMTGS_COIN_1601",
        "α类新年寻访凭证（2020）": "2020recruitment10_1",
        "β类新年寻访凭证（2020）": "2020recruitment10_2",
        "γ类新年寻访凭证（2020）": "2020recruitment10_3",
        "α类新年寻访凭证（2021）": "2021recruitment10_1",
        "β类新年寻访凭证（2021）": "2021recruitment10_2",
        "γ类新年寻访凭证（2021）": "2021recruitment10_3",
    }
    _ = os.path
    _PARENT = _.realpath(_.join(_.dirname(__file__), '..'))
    unknown_item = []
    err_k = []
    for name, rarity, url, sortid in item_dump:
        # http://prts.wiki/images/thumb/2/23/%E9%81%93%E5%85%B7_%E5%B8%A6%E6%A1%86_%E6%97%A0%E5%90%8D%E7%9A%84%E8%AF%86%E5%88%AB%E7%89%8C.png/100px-%E9%81%93%E5%85%B7_%E5%B8%A6%E6%A1%86_%E6%97%A0%E5%90%8D%E7%9A%84%E8%AF%86%E5%88%AB%E7%89%8C.png
        # http://prts.wiki/images/2/23/%E9%81%93%E5%85%B7_%E5%B8%A6%E6%A1%86_%E6%97%A0%E5%90%8D%E7%9A%84%E8%AF%86%E5%88%AB%E7%89%8C.png
        # if image in current path,break
        try:
            id_ = item_names.get(name)
            if id_ is None:
                id_ = patch_item_name_data.get(name)
                if id_ is None:
                    id_ = name
                    unknown_item.append(id_)
                    logger.warning("[ItemIconUpdater]无效的材料转换名称:" + name)
            if os.path.exists(f"{_PARENT}\\imgReco\\img\\lootitem\\{id_}.png"):
                continue
            url_new = url.replace("/thumb", "")[::-1].split("/", 1)[1][::-1]
            rep = requests.get(url_new, headers=headers)
            if rep.status_code == 200:
                logger.notice(f"[ItemIconUpdater]完成图标更新: {id_}")
                with open(f"{_PARENT}\\imgReco\\img\\lootitem\\{id_}.png", "wb") as f:
                    f.write(rep.content)
        except:
            logger.error("出现错误：" + str([name, rarity, url, sortid]))
            err_k.append([name, rarity, url, sortid])
    print(unknown_item)
    print(err_k)
