from utils.utils import PushableDict


class StageDropInfo(dict):
    dropType = {
        -1: '攻击奖励',
        0: 'UNKNOWN-0',
        1: '首次掉落/干员&家具',
        2: '常规掉落',
        3: '特殊掉落',
        4: '额外物资',
        5: 'UNKNOWN-5',
        6: 'UNKNOWN-6',
        7: 'UNKNOWN-7',
        8: '首次掉落/至纯源石',
        9: 'UNKNOWN-9',
        252: '理智返还',
        253: 'UNSET_MATERIAL',
        254: 'RECOGNIZE_FAIL',

    }
    dropTypeColor = {  # type bgr
        -1: (0, 214, 253),
        0: (0, 0, 0),
        1: (0, 0, 0),
        2: (175, 175, 175),
        3: (82, 120, 178),  # fake!
        4: (53, 227, 218),
        5: (0, 0, 0),
        6: (0, 0, 0),
        7: (0, 0, 0),
        8: (-1, -1, -1),
        9: (0, 0, 0),
        252: (220, 220, 220),
        253: (0, 0, 0),
        254: (0, 0, 0),
    }

    def __init__(self, *args, **kwargs):
        super(StageDropInfo, self).__init__(*args, **kwargs)

    def getDropList(self, filter_char=True, filter_furn=True):
        drop_list = {(i['dropType'], i['id'],) for i in self["displayDetailRewards"] if
                     (i["type"] != "CHAR" or not filter_char) and (i["type"] != "FURN" or filter_furn)}
        drop_list.add((-1, '4001',))
        drop_list.add((-1, '5001',))
        return drop_list


class StageInfo(dict):
    def __init__(self, *args, **kwargs):
        super(StageInfo, self).__init__(*args, **kwargs)

    def getDropInfo(self):
        return StageDropInfo(self["stageDropInfo"])

    def getName(self):
        return self['name']

    def getCode(self):
        return self['code']

    def getCost(self):
        return self['apCost'], self['etCost']

    def getFailReturn(self):
        return self['apFailReturn'], self['etFailReturn']


class StageExcel(dict):
    def __init__(self, *args, **kwargs):
        super(StageExcel, self).__init__(*args, **kwargs)

    def getStage(self, stageCode, stageName=None):
        if stageCode is None:
            if stageName is None:
                raise ValueError("stageCode and stageName cannot both be None!")
            for k, v in self['stages'].items():
                if v['name'] == stageName and "#f#" not in k:
                    return StageInfo(v)
            raise ValueError(f"{'' if stageName is None else f'name {stageName}'} doesn't exist in current Stages")
        else:
            for k, v in self['stages'].items():
                if v['code'] == stageCode and (stageName is None or v['name'] == stageName) and "#f#" not in k:
                    return StageInfo(v)

        raise ValueError(f"{stageCode} "
                         f"{'' if stageName is None else f'with {stageName}'} doesn't exist in current Stages")
