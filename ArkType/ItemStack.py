# item_table.json ->物品
# building_data.json [workshopFormulas] -> 合成配方
from utils.logger import root_logger as logger
from ArkTagData.TagGetter import getItemNameDict, getItemTag, getFurniItemNameDict, \
    getRogueLikeItemNameDict, getCharNameDict, getSkinNameDict
from ArkType.StageExcel import StageDropInfo


class ItemType:
    NONE = 0
    CHAR = 1  # 角色
    CARD_EXP = 2
    MATERIAL = 3
    GOLD = 4
    EXP_PLAYER = 5
    TKT_TRY = 6
    TKT_RECRUIT = 7
    TKT_INST_FIN = 8
    TKT_GACHA = 9
    ACTIVITY_COIN = 10
    DIAMOND = 11
    DIAMOND_SHD = 12
    HGG_SHD = 13
    LGG_SHD = 14
    FURN = 15  # 家具
    AP_GAMEPLAY = 16
    AP_BASE = 17
    SOCIAL_PT = 18
    CHAR_SKIN = 19
    TKT_GACHA_10 = 20
    TKT_GACHA_PRSV = 21
    AP_ITEM = 22
    AP_SUPPLY = 23
    RENAMING_CARD = 24
    ET_STAGE = 25
    ACTIVITY_ITEM = 26
    VOUCHER_PICK = 27
    VOUCHER_CGACHA = 28
    VOUCHER_MGACHA = 29
    CRS_SHOP_COIN = 30
    CRS_RUNE_COIN = 31
    LMTGS_COIN = 32
    EPGS_COIN = 33
    LIMITED_TKT_GACHA_10 = 34
    LIMITED_FREE_GACHA = 35
    REP_COIN = 36
    ROGUELIKE = 37  # 肉鸽物品


class ItemStack(dict):
    __itemType__ = ItemType()
    __roguList__ = getRogueLikeItemNameDict()
    __itemList__ = getItemNameDict()
    __charList__ = getCharNameDict()
    __skinList__ = getSkinNameDict()
    __furnList__ = getFurniItemNameDict()
    __allKnownFields__ = [__itemList__, __furnList__, __charList__, __skinList__, __roguList__]
    __itemtag__ = getItemTag()["items"]

    def __init__(self, *val, **kwargs):
        # ItemStack({"扭转醇":1})
        # ItemStack(扭转醇=1,...)
        # ItemStack("扭转醇:1","固源岩:1")
        if len(val) == 0:
            super(ItemStack, self).__init__()
        elif isinstance(val[0], dict):
            super(ItemStack, self).__init__(val[0])
        elif isinstance(val[0], str):
            _MT = {}
            for value in val:
                try:
                    k, v = value.replace('=', ':').split(":")
                    _MT.update({k: float(v)})
                except ValueError:
                    logger.error(f"Unresolved string:{value},expect \'NAME:NUM\' or \'NAME=NUM\'")
            super(ItemStack, self).__init__(_MT)
        self.addItemFromDict(kwargs)
        self._check_value()

    def raiser(self, other, operation):
        raise TypeError(f"'{operation}' not supported between instances of '{self.__class__.__name__}'"
                        f" and '{other.__class__.__name__}'")

    def _check_value(self):
        for k, v in self.items():
            if isinstance(v, (int, float)):
                continue
            if isinstance(v, str):
                try:
                    self[k] = float(v)
                except:
                    logger.error(f"cannot convert {v} to an float format. remove {k} instead")
                    self.pop(k)

    def _direct_add(self, name, quantity):
        self.update({name: self.get(name, 0) + quantity})
        if self.get(name) == 0:
            self.pop(name)
        return self

    def addItems(self, droplist=None):
        if droplist is not None:
            for _ in droplist:
                self.addItem(_["name"], _["quantity"])
        return self

    def addRawItem(self, raw_name, quantity):
        for field in self.__allKnownFields__:
            realName = field.get(raw_name, None)
            if realName is not None:
                return self._direct_add(realName, quantity)
        logger.error(f"0:不存在名为'{raw_name}'的物品")
        return self

    def addItem(self, name, quantity, check=True):
        if not check:
            return self._direct_add(name, quantity)
        for field in self.__allKnownFields__:
            if name in field.values():
                return self._direct_add(name, quantity)
        logger.error(f"0:不存在名为'{name}'的物品")
        return self

    def autoAddItem(self, name, quantity):
        for field in self.__allKnownFields__:
            if name in field.values():
                return self._direct_add(name, quantity)
        for field in self.__allKnownFields__:
            realName = field.get(name, None)
            if realName is not None:
                return self._direct_add(realName, quantity)
        logger.error(f"-1:不存在名为'{name}'的物品")
        return self

    def addItemFromRawDictList(self, dumplist: list):
        for val in dumplist:
            self.addItemFromRawDict(val)
        return self

    def addItemFromRawDict(self, dumpdict: dict):
        if dumpdict.get('type') in ['FURN', 'CHAR', 'NONE', 'ET_STAGE']:
            logger.warning(f"cannot add type:{dumpdict.get('type')} into ItemStack")
            return self
        try:
            return self.addItem(getItemTag()['items'].get(dumpdict.get('id'))['name'], int(dumpdict.get('count')))
        except:
            logger.warning(f"cannot add [T:{dumpdict.get('type')} I:{dumpdict.get('id')}] into ItemStack")
        return self

    def addItemFromDict(self, dictobj):
        for k, v in dictobj.items():
            self.autoAddItem(k, v)
        return self

    def addItemFromCharCost(self, cost):
        self.addItem(self.__itemtag__[cost["id"]]['name'], cost['count'])
        return self

    # def addItemFromDropReco(self,reco_list):

    def addItemFromList_NameQuantity(self, li: list):
        for name, quantity in li:
            self.addItem(name, quantity)
        return self

    def registItem(self, drop_list, value=1):
        if isinstance(drop_list, (list, set)):
            for _id, name in drop_list:
                self.addItem(name, value)
        elif isinstance(drop_list, str):
            self.addItem(drop_list, value)
        return self

    def delItem(self, k):
        if self.get(k, None) is not None:
            return self.pop(k)
        return None

    def __contains__(self, item):
        if isinstance(item, (dict, list)):
            for _ in item:
                if _ not in self:
                    return False
            return True
        if isinstance(item, str):
            if self.get(item, None) is not None:
                return True
            return False

    def formatItems(self, format_='%item%(%quantity%) ', skip_zero=True):
        format_ = format_.replace('%item%', '{item}').replace('%quantity%', '{quantity}')
        opt_ = ''
        for item, quantity in self.items():
            if quantity == 0 and skip_zero:
                continue
            opt_ += format_.format(item=item, quantity=quantity)
        return opt_

    def format_rich(self):
        _ = []
        for k_name, v_quantity in self.items():
            _.append(f"[yellow1]{k_name}[/]([blue]{v_quantity}[/])")
        return "Items{" + ' '.join(_) + '}'

    def __add__(self, other):
        if isinstance(other, ItemStack):
            that = self.copy()
            for k, v in other.items():
                that.update({k: that.get(k, 0) + v})
            return ItemStack(that)
        elif isinstance(other, DropItemStack):
            that = self.copy()
            for k, v in other.items():
                for name, quantity in v:
                    that.update({name: that.get(name, 0) + quantity})
            return ItemStack(that)
        raise ValueError('other expected a ItemStack-Type')

    def __sub__(self, other):
        if isinstance(other, ItemStack):
            that = self.copy()
            for k, v in other.items():
                if self.get(k, None) is None:
                    continue
                val = self.get(k) - v
                if val > 0:
                    that.setdefault(k, val)
                else:
                    that.pop(k)
            return ItemStack(that)
        raise ValueError('other expected a ItemStack-Type')

    # def __eq__(self, other):
    #     print('__eq__ function is proceeded!')
    #
    # def __ne__(self, other):
    #     print('__nq__ function is proceeded!')

    def __gt__(self, other):
        # self > other called
        if not isinstance(other, (dict, int)):
            self.raiser(other, ">")
        for k, v in self.items():
            if v <= other.get(k, 0):
                return False
        return True

    def __ge__(self, other):
        # self >= other called
        if not isinstance(other, (dict, int)):
            self.raiser(other, ">=")
        for k, v in self.items():
            if v < other.get(k, 0):
                return False
        return True

    def __lt__(self, other):
        # self < other called
        if not isinstance(other, (dict, int)):
            self.raiser(other, "<")
        for k, v in self.items():
            if v >= other.get(k, 0):
                return False
        return True

    def __le__(self, other):
        # self <= other called
        if not isinstance(other, (dict, int)):
            self.raiser(other, "<=")
        for k, v in self.items():
            if v > other.get(k, 0):
                return False
        return True

    def __str__(self):
        if self:
            return super(ItemStack, self).__str__().replace('\'', '').replace(' ', '')
        else:
            return '{无掉落物}'


class DropItemStack(dict):
    def __init__(self, *args, **kwargs):
        super(DropItemStack, self).__init__(*args, **kwargs)

    def addItem(self, name, quantity, type_=253):
        if self.get(type_, None) is None:
            self.setdefault(type_, list())
        if quantity != 0:
            self[type_].append([name, quantity])

    def getAllItems(self):
        u = []
        for t, i in self.items():
            for n, q in i:
                u.append([n, q, t])
        return u

    def format_rich(self):
        _ = []
        for k_type, v_li in self.items():
            __ = []
            for name, quantity in v_li:
                __.append(f"[yellow1]{name}[/]([blue]{quantity}[/])")
            _.append(f"[orange1]{StageDropInfo.dropType.get(k_type)}[/][{' '.join(__)}]")
        return f"DropItems{{{' '.join(_)}}}"

    def __str__(self):
        _ = []
        for k_type, v_li in self.items():
            __ = []
            for name, quantity in v_li:
                __.append(f"{name}({quantity})")
            _.append(f"{StageDropInfo.dropType.get(k_type)}[{' '.join(__)}]")
        return "DropItems{" + ' '.join(_) + '}'
