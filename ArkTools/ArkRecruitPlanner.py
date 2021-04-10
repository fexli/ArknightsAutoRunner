import itertools
import time
from ArkTagData import TagGetter
from utils.utils import removeItemFromList, removeItemsFromList
import numpy as np


def popNoneInList(List):
    return [i for i in List if i is not None]


def replaceAka(tagList):
    aka = TagGetter.getRecruitAkaTag()
    return popNoneInList(aka.wheres(tagList))


def planRecruit(tagListIfAka, can_refresh=False):
    tagList = replaceAka(tagListIfAka)
    s_t = time.time()
    recruit = []
    charRateTag = TagGetter.getCharRateTag()
    recruitTag = TagGetter.getRecruitTag()
    for i in range(len(tagList)):
        for tags in itertools.combinations(tagList, i + 1):
            # tags ->("Tag1","<Tag2>",...)
            if len(tags) == 1:
                recruit.append([tags, recruitTag[tags[0]]])
            else:
                kv = [recruitTag[v] for v in tags]
                recruit.append([tags, list(set(recruitTag[tags[0]]).intersection(*kv))])
    # 计算优先度
    final = []
    for _ in recruit:
        if _[1]:
            # 按照平均度计算分数
            rarities = charRateTag.wheres(_[1])
            # 如果没有高级资深干员，则删掉队列中rarity=6的角色
            if "高级资深干员" in _[0]:
                charList = _[1]
                recruit_type = 1  # 出现高级资深干员,9H
            elif "支援机械" in _[0]:
                recruit_type = 2  # 出现支援机械TAG,3H50M
                charList = list(filter(lambda x: rarities[_[1].index(x)] != 6, _[1]))
                rarities = removeItemFromList(rarities, 6)
                rarities = removeItemsFromList(rarities)
            elif "新手" in _[0]:
                recruit_type = 0  # 正常,9H
                charList = list(filter(lambda x: rarities[_[1].index(x)] != 6, _[1]))
                rarities = removeItemFromList(rarities, 6)
            else:
                recruit_type = 0  # 正常,9H
                charList = list(filter(lambda x: rarities[_[1].index(x)] != 6, _[1]))
                rarities = removeItemFromList(rarities, 6)
                rarities = removeItemsFromList(rarities, 1, 2)
            try:
                low_rate = min(rarities)
            except ValueError:
                continue  # such as ["支援","重装干员"] cost ValueError because rarities.len is 0
            score = np.average(rarities) + len(_[0]) * 0.1 + min(rarities) - 5 - len(
                charList) * 0.03  # * (-1 ** recruit_type)
            final.append({"tags": _[0],
                          "score": score,
                          "chars": charList,
                          "type": recruit_type,
                          "low_rarity": low_rate,
                          "rarities": rarities})

    final = sorted(final, key=lambda x: -x["score"])
    # 对全体TAG池进行匹配
    best = []
    for _ in final:
        if _.get("type") == 1:
            best = _
            break
        if _.get("low_rarity") == 5:
            best = _
            break
        if _.get("type") == 2:
            best = _
            break
        if _.get("low_rarity") == 4:
            best = _
            break
    if can_refresh:
        decision = {"action": "refresh"}
    else:
        decision = {"action": "exit"}
    if best:
        decision = {"action": "choose",
                    "tag": [tagList.index(index) for index in best.get("tags")],
                    "time": [(9, 0), (9, 0), (3, 5)][best.get("type")]}
    end = time.time() - s_t
    return {"raw_input": tagListIfAka,
            "input": tagList,
            "raw_output": recruit,
            "output": final,
            "best": best,
            "decision": decision,
            "cost": end}
