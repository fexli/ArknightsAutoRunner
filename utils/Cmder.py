from .Job import stop_thread, Job
import time
from .logger import root_logger as logger
import sys


# 指令添加类
class cmdlist():
    def __init__(self):
        self._cmdlist = []
        self.__index = -1

    def __iter__(self):
        self.__index = -1
        return self

    def __next__(self):
        self.__index = self.__index + 1
        if self.__index < self._cmdlist.__len__():
            return self._cmdlist[self.__index]
        else:
            raise StopIteration

    def addCmd(self, name, func, help):
        try:
            setattr(self, name, cmdlist._simpleCommander(func, help))
            self._cmdlist.append(name)
            return True
        except:
            return False

    def getCmd(self, name):
        if name in self._cmdlist:
            return getattr(self, name).function
        else:
            return None

    def getHelp(self, name):
        if name in self._cmdlist:
            return getattr(self, name).help
        else:
            return "不存在指令%s" % name

    class _simpleCommander():
        def __init__(self, func, help):
            self.function = func
            self.help = help


# 指令输入
class commander:
    help_print = "{0:15}\t{1:15}"

    def __init__(self):
        self._cmdList = cmdlist()
        self._exitcmdList = cmdlist()
        self._running = False
        self._has_job = False
        self._job_type = 0
        self._job_cmd = None
        self._nowtarget = None
        self._last_job_return = None
        self.Job = Job(target=self.Listener)
        self.createCommand('help', 'h', function=self.cmdHelp, help='执行帮助')
        self.createCommand('stopnow', 'sn', function=None, help='强制结束当前任务')

    def clearNowjob(self):
        self._has_job = False
        self._job_cmd = None
        self._job_type = 0

    def get_latest_job_return(self):
        while self._has_job:
            time.sleep(0.03)
        return self._last_job_return

    def todo(self):
        while True:
            self._nowtarget.wait()
            if self._has_job:
                if self._job_type == 2:
                    try:
                        self._last_job_return = self._cmdList.getCmd(self._job_cmd)()
                    except Exception as e:
                        self._last_job_return = None
                        logger.error(f"Command Exception(in {self._job_cmd}):{e}")
                elif self._job_type == 1:
                    try:
                        self._last_job_return = self._cmdList.getCmd(self._job_cmd[0])(self._job_cmd[1])
                    except Exception as e:
                        self._last_job_return = None
                        logger.error(
                            f"Command Exception(in {self._job_cmd[0]} with args={str(self._job_cmd[1])}):{e}")
                self.clearNowjob()
            else:
                self._nowtarget.pause()
            time.sleep(0.1)

    def cmdHelp(self, *helpname):
        if helpname:
            logger.help(self.help_print.format(helpname[0], str(self._cmdList.getHelp(helpname[0])), chr(12288)))
            # logger.help(helpname[0] + ":\t\t\t" + str(self._cmdList.getHelp(helpname[0])))

        else:
            for helpn in self._cmdList:
                logger.help(self.help_print.format(helpn, str(self._cmdList.getHelp(helpn)), chr(12288)))
                # logger.help(helpn + ":\t\t\t" + str(self._cmdList.getHelp(helpn)))

    def _regCmd(self, name, func, help, exitcmd=False):
        if exitcmd:
            if self._exitcmdList.addCmd(name, func, help):
                return 0
            else:
                return '无法注册！%s' % name  # 无法注册
        if name in self._cmdList:
            return '已存在名为%s的指令' % name  # 存在指令名
        else:
            if self._cmdList.addCmd(name, func, help):
                return 0
            else:
                return '无法注册！%s' % name  # 无法注册

    def createExitCommand(self, *command, function, help=None):
        for c in command:
            ret = self._regCmd(c, function, help, exitcmd=True)
            if not ret == 0:
                logger.error(ret)

    def createCommand(self, *command, function, help=None):
        for c in command:
            ret = self._regCmd(c, function, help)
            if not ret == 0:
                logger.error(ret)

    def readCmd(self, cmdin):
        if self._nowtarget is None:
            logger.error("commander not running, use StartTrack() to run.")
            return None
        cmdin = cmdin.split(' ')
        if cmdin[0] == 'stopnow' or cmdin[0] == 'sn':
            if self._has_job:
                logger.warning('正在强制停止当前任务中')
                self.clearNowjob()
                stop_thread(self._nowtarget)
                time.sleep(0.15)
                self._nowtarget = Job(target=self.todo)
                self._nowtarget.start()
                logger.warning('已强制停止当前任务')
            else:
                logger.warning('当前无执行中的任务')
        elif self._has_job:
            logger.error('还有正在运行的指令！请稍后')
        else:
            if cmdin[0] in self._exitcmdList:
                cmd = cmdin.pop(0)
                cmd_itr = ''
                for c in cmdin:
                    cmd_itr = cmd_itr + c + ' '
                if not cmd_itr == '':
                    cmd_itr = cmd_itr[:-1]
                    logger.system('运行退出指令：%s %s' % (cmd, cmd_itr))
                    self._exitcmdList.getCmd(cmd)(cmd_itr)
                else:
                    logger.system('运行退出指令：%s' % (cmd))
                    self._exitcmdList.getCmd(cmd)()
            elif cmdin[0] in self._cmdList:
                cmd = cmdin.pop(0)
                cmd_itr = ''
                for c in cmdin:
                    cmd_itr = cmd_itr + c + ' '
                if not cmd_itr == '':
                    cmd_itr = cmd_itr[:-1]
                    logger.system('运行指令：%s %s' % (cmd, cmd_itr))
                    self._has_job = True
                    self._job_type = 1
                    self._nowtarget.resume()
                    self._job_cmd = [cmd, cmd_itr]
                    # self._cmdList.getCmd(cmd)(cmd_itr)
                else:
                    logger.system('运行指令：%s' % (cmd))
                    self._has_job = True
                    self._job_type = 2
                    self._nowtarget.resume()
                    self._job_cmd = cmd
                    # self._cmdList.getCmd(cmd)()
            else:
                logger.error('未知指令%s' % cmdin[0])

    def Listener(self):
        while True:
            r = input()
            self.readCmd(r)

    def Listener_withoutinput(self):
        while True:
            line = sys.stdin.readline().strip()
            if not line:
                break
            else:
                self.readCmd(line)

    def StartTrack(self, splogin=False):
        if not self._running:
            if splogin is False:
                self.Job = Job(target=self.Listener)
                self.Job.start()
                self._nowtarget = Job(target=self.todo)
                self._nowtarget.start()
            else:
                self.Job = Job(target=self.Listener_withoutinput)
                self.Job.start()
                self._nowtarget = Job(target=self.todo)
                self._nowtarget.start()
            self._running = True

    def StopTrack(self):
        if self._running:
            logger.notice('Cmder的计时器"Job"停止中...')
            stop_thread(self.Job)
            logger.notice('Cmder的计时器"Job"已停止')
            self._nowtarget.stop()
            stop_thread(self._nowtarget)
            logger.notice('Cmder的计时器"target"已停止')
            self._running = False
