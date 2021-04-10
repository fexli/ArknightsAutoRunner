import time
from utils.logger import root_logger as logger
from utils.Job import Job, stop_thread


def appender(parent):
    root_time = time.time()
    last_cover = time.time()
    next_duration = 6 * 60
    # TODO:满体力检测
    while parent.running:
        time.sleep(next_duration - 0.01)
        parent.intellect += 1
        cover_time = time.time() - last_cover
        if cover_time > 6 * 60 + 0.5:
            # 电脑睡眠唤醒后时间跨度
            logger.notice("检测到程序终止跨度：%d" % int(cover_time))
            int_add = 0
            while cover_time >= 6 * 60:
                cover_time -= 6 * 60
                parent.intellect += 1
                int_add += 1
            logger.notice("期间恢复%d理智" % int_add)
            last_cover = time.time() - cover_time - 0.01
            next_duration = 6 * 60 - cover_time
        else:
            last_cover = time.time()
            next_duration = 6 * 60


class PlayerConfig(object):
    def __init__(self, intellect, max_intellect):
        self.running = True
        self.intellect = int(intellect)
        self.max_intellect = int(max_intellect)
        self.task = Job(target=appender, args=(self,))
        self.task.start()
        self.in_operation = False
        self.operation_cost = 0
        # TODO:门票类型设置

    def update(self, current, max_=None):
        self.intellect = int(current)
        if max_ is not None:
            self.max_intellect = int(max_)
        return self

    def stop(self):
        self.running = False
        stop_thread(self.task)

    def take(self, i):
        self.intellect -= int(i)
        return self.intellect

    def give(self, i):
        self.intellect += int(i)
        return self.intellect

    def have(self, i):
        return self.intellect >= int(i)

    def restore(self):
        self.intellect += self.max_intellect
        return self.intellect

    def startOperation(self, cost, use_any_suply=False):
        if self.in_operation:
            logger.debug("正在作战中！")
            return True
        if self.have(cost):
            self.intellect -= 1
            self.in_operation = True
            self.operation_cost = cost
            logger.debug(f"当前持有理智({self.intellect})>消耗({cost}),允许开始作战。")
            return True
        if use_any_suply:
            logger.debug("持有理智不足但允许使用回复，允许开始作战。")
            return True
        logger.debug(f"当前持有理智({self.intellect})<消耗({cost})且不允许使用回复,禁止开始作战。")
        return False

    def endOperation(self):
        logger.debug("结束作战！")
        self.intellect = self.intellect - self.operation_cost + 1
        self.operation_cost = 0
        self.in_operation = False
        return True

    def stopOperation(self, deduction=0, show=False):
        if self.in_operation:
            if show:
                logger.debug("强制结束作战(退出/非3星作战)")
            self.intellect -= deduction
            self.operation_cost = 0
            self.in_operation = False
        return True
