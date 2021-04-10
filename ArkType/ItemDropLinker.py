import os
import time
import typing
from ArkType.AttackInfo import DropInfo
from ArkType.ItemStack import DropItemStack
from ArkTagData.TagGetter import getStageTag, getItemTag
from utils.logger import root_logger as logger
from utils.utils import randomstr

DROPFOLDER_PATH = '.\\Drop\\'


class ItemDropLinker:

    def __init__(self, config='.\\Drop\\.cfg'):
        self._li = {}
        self.booster = 0
        self._config = config
        if not os.path.exists(config):
            os.makedirs(os.path.dirname(config), exist_ok=True)
            with open(config, 'wb') as f:
                pass
        with open(config, 'rb') as f:
            while (_klen := f.read(2)) != b'':
                # _id = int.from_bytes(f.read(2),'little')
                _keyw = f.read(int.from_bytes(_klen, 'little')).decode(encoding='utf-8')
                self._li.setdefault(_keyw, self.booster)
                self.booster += 1

    def get(self, key: typing.Union[str, int], create=True):
        if isinstance(key, int):
            for k, v in self._li.items():
                if v == key:
                    return k
            return f"unknown-item-id{key}"
        elif isinstance(key, str):
            if key not in self._li:
                if create:
                    self._li.setdefault(key, self.booster)
                    with open(self._config, 'ab') as f:
                        _key_enc = key.encode(encoding='utf-8')
                        f.write(len(_key_enc).to_bytes(2, 'little'))
                        f.write(_key_enc)
                    self.booster += 1
                    return self.booster - 1
                else:
                    return -1
            else:
                return self._li.get(key)

    def writeStageDrop(self, stageId: str, dropList: dict, cost_time: float = 0):
        return getattr(self, f"_writeStageDrop_Ver{2}")(stageId, dropList, cost_time)
        # return self._writeStageDrop_Ver1(stageId, dropList)

    def _writeStageDrop_Ver1(self, stageId: str, dropList: dict, cost_time: float = 0):
        """
        :param stageId: type str for read file {stageId}.drp
        :param dropList: recognizeEndItemsWithTag() return's
        :return: None
        :writeStructure: ([version \x01][len(droplist)<1>][[itemid<2>][quantity<2>]]..[time<4>])
        """
        sv = []
        for i in dropList:
            if i['have']:
                _q = i['quantity']
                if _q > 0:
                    sv.append([self.get(i['name']), _q])
        if len(sv) == 0:
            logger.warning(f"EMPTY DropList as Stage<{stageId}>")
            return
        with open(f"{DROPFOLDER_PATH}{stageId}.drp", 'ab') as fd:
            fd.write(b'\x01')
            fd.write(len(sv).to_bytes(1, 'little'))
            for i, q in sv:
                fd.write(i.to_bytes(2, 'little'))
                fd.write(q.to_bytes(2, 'little'))
            fd.write(int(time.time()).to_bytes(4, 'little'))

    def _writeStageDrop_Ver2(self, stageId, dropList, cost_time: float = 0, raw_finish_time: int = 0):
        """
        :param stageId: type str for read file {stageId}.drp
        :param dropList: recognizeEndItemsWithTag() return's
        :param cost_time: cost time of attack
        :param raw_finish_time:原始完成时间
        :return: None
        :writeStructure: ([version \x02][len(droplist)<1>][[itemid<2>][quantity<2>][type<1>]]..[atk_time<3>][time<4>])
        """
        sv = []
        for i in dropList:
            _q = i['quantity']
            if _q > 0:
                sv.append([self.get(i['name']), _q, i['type']])
        if len(sv) == 0:
            logger.warning(f"EMPTY DropList as Stage<{stageId}>")
            return
        with open(f"{DROPFOLDER_PATH}{stageId}.drp", 'ab') as fd:
            fd.write(b'\x02')
            fd.write(len(sv).to_bytes(1, 'little'))
            for i, q, t in sv:
                fd.write(i.to_bytes(2, 'little'))
                fd.write(q.to_bytes(2, 'little'))
                fd.write((t + 1).to_bytes(1, 'little'))
            try:
                fd.write(int(cost_time * 100).to_bytes(3, 'little'))
            except OverflowError:
                logger.warning(f"cannot convert cost_time({cost_time}) into byte!")
                fd.write(b'\xff\xff\xff')
            fd.write(int(raw_finish_time or time.time()).to_bytes(4, 'little'))

    def getStageDrop(self, stageId: str):
        if not os.path.isfile(f"{DROPFOLDER_PATH}{stageId}.drp"):
            return list()
        data = []
        with open(f"{DROPFOLDER_PATH}{stageId}.drp", 'rb') as f:
            while (_ver := f.read(1)) != b'':
                try:
                    data.append(self._parseGetStageDrop(_ver)(stageId, f))
                except AttributeError:
                    logger.error(f"got Unparsed data at {len(data) + 1},Version={_ver}. break")
                    break
        return data

    def _parseGetStageDrop(self, ver: bytes):
        ver = int.from_bytes(ver, 'little')
        try:
            return getattr(self, f"_getStageDrop_Ver{ver}")
        except AttributeError:
            logger.error(f"解析中断：未知的关卡掉落解析器版本：Ver{ver}")
            raise AttributeError(f"Unknown Parser Version:{ver}")

    def _getStageDrop_Ver1(self, stageId: str, f):
        ttl_item_len = int.from_bytes(f.read(1), 'little')
        stack = DropItemStack()
        for _ in range(ttl_item_len):
            name = self.get(int.from_bytes(f.read(2), 'little'))
            quantity = int.from_bytes(f.read(2), 'little')
            stack.addItem(name, quantity)
        atk_time = int.from_bytes(f.read(4), 'little')
        return DropInfo(1, stageId, atk_time, stack)

    def _getStageDrop_Ver2(self, stageId: str, f):
        ttl_item_len = int.from_bytes(f.read(1), 'little')
        stack = DropItemStack()
        for _ in range(ttl_item_len):
            name = self.get(int.from_bytes(f.read(2), 'little'))
            quantity = int.from_bytes(f.read(2), 'little')
            type_ = int.from_bytes(f.read(1), 'little') - 1
            stack.addItem(name, quantity, type_)
        atk_ingame_time = int.from_bytes(f.read(3), 'little') / 100
        atk_time = int.from_bytes(f.read(4), 'little')
        return DropInfo(2, stageId, atk_time, stack, atk_ingame_time)
    # STAGE_DROP_PARSER = [_getStageDrop_Ver1]
    # STAGE_DROP_ENCODER = [_writeStageDrop_Ver1]


def UpgradeDropFromVer1_ToVer2(ark, stage, force=False):
    drp = getStageTag().getStage(stage).getDropInfo().getDropList()
    li = list(i[1] for i in drp)
    se = set(i[1] for i in drp)
    if len(li) != len(se):
        logger.warning('Unable to upgrade the level with different drop overlaps from Ver.1 to Ver.2!')
        if not force:
            return False
    drop_info = ark.dropLinker.getStageDrop(stage)
    drp_wname = {}
    for drop_type, game_id in drp:
        drop_name = getItemTag()['items'].get(game_id)['name']
        drop_id = ark.dropLinker.get(drop_name)
        drp_wname.update({drop_name: [drop_name, drop_id, drop_type]})
    for index in range(len(drop_info)):
        cur_drop: DropInfo = drop_info[index]
        if cur_drop.getVersion() != 1:
            continue
        if cur_drop.isEmpty():
            logger.warning(f"Find Empty Attack at Index:{index} in Stage:{stage},Set to None.")
            drop_info[index] = None
            continue
        new_drop = DropItemStack()
        ERR_G = [None, None, None]
        for type_, drp_li in cur_drop.dropList.items():
            for drp_name, drop_q in drp_li:
                new_drop.addItem(drp_name, drop_q, drp_wname.get(drp_name, ERR_G)[2] or 253)

        drop_info[index] = DropInfo(2, stage, cur_drop.attackTime, new_drop)
    # Write file Structure:([version \x02][len(droplist)<1>][[itemid<2>][quantity<2>][type<1>]]..[atk_time<3>][time<4>])
    # save raw file to backup
    os.rename(f"{DROPFOLDER_PATH}{stage}.drp", f"{DROPFOLDER_PATH}{stage}.drp.U12.{randomstr()}")
    ttl_upg = 0
    with open(f"{DROPFOLDER_PATH}{stage}.drp", 'wb') as fd:
        for dropstack in drop_info:
            if dropstack is None:
                continue
            fd.write(b'\x02')
            all_items = dropstack.dropList.getAllItems()
            fd.write(len(all_items).to_bytes(1, 'little'))
            for name, quantity, type_ in all_items:
                fd.write(ark.dropLinker.get(name).to_bytes(2, 'little'))
                fd.write(quantity.to_bytes(2, 'little'))
                fd.write((type_ + 1).to_bytes(1, 'little'))
            cost_time = dropstack.atk_in_t or 0
            try:
                fd.write(int(cost_time * 100).to_bytes(3, 'little'))
            except OverflowError:
                logger.warning(f"cannot convert cost_time({cost_time}) into byte!")
                fd.write(b'\xff\xff\xff')
            fd.write(dropstack.attackTime.to_bytes(4, 'little'))
            ttl_upg += 1
    logger.notice(f"Upgrade Finished![STAGE {stage},{ttl_upg}TUI]")
    return drop_info
