from ArkType.ItemStack import DropItemStack, ItemStack
import typing
import time


class DropInfo:
    def __str__(self):
        return f"DropInfo<{self._version}> in {self.stage}{f'[cost {self.atk_in_t}s]' if self.atk_in_t else ''}" \
               f" Drop{self.dropList} at {time.ctime(self.attackTime)}"

    def __init__(self, version: int, stageId: str, attackTime: int,
                 dropList: typing.Union[DropItemStack, ItemStack] = None,
                 atk_ingame_time: float = 0):
        self._version = version
        self.attackTime = attackTime
        self.stage = stageId
        self.dropList = dropList or DropItemStack()
        self.atk_in_t = atk_ingame_time

    def addDropItem(self, item, quantity, type_=253):
        self.dropList.addItem(item, quantity, type_)

    def getVersion(self):
        return self._version

    def isEmpty(self):
        return not bool(self.dropList)

    def getByType(self, type_):
        return self.dropList.get(type_, list())
