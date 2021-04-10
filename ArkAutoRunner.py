from ArkTools.ArkRecruitPlanner import planRecruit
from ArkTagData.TagGetter import *
from ArkType.ItemStack import ItemStack
from ArkType.StageSet import StageSet
from ArkType.StageExcel import StageInfo
from ArkType.ItemDropLinker import ItemDropLinker
from ArkMapping import Mapping
from ArkMapping.ArkMap import ArkMap
from ArkPlanner.MaterialPlanning import MaterialPlanning
from connector.ADBConnector import ADBConnector, ensure_adb_alive
from utils.utils import getLogFileName, time_sleep
from utils.Clicker import Clicker
from utils.MumuScreenShot import *
from utils.formater import formatDropItem
from utils.Job import Job, stop_thread
from utils.Cmder import commander
from imgReco.operationReco import load_data as getReconizer
from imgReco.operationReco import *
from imgReco.waitingReco import *
from imgReco.gameTemplate import GameTemplate
from imgReco.recruitReco import *
from imgReco.gachaReco import getRecruitDetail
from imgReco.mapReco import *
from imgReco.taskReco import *
from config.PlayerConfig import PlayerConfig
from config.Statics import EXTER_CLICK_DATA, MIN_ENABLE_EXTER_ATK_CAMP_NUM
import time
import sys
from PIL import Image
from pathlib import Path
import traceback

logger.system("欢迎使用ArknightsAutoTools")
VERSION = '0.1.25'


def ark_job_runnger(func, ark_main, typ, cover_result=False):
    _s = time.time()
    try:
        result = func()
        logger.system(f"线程执行完成(共耗时{time.time() - _s:2f}s)")
    except Exception as e:
        logger.error(f"线程运行出现错误(已运行{time.time() - _s:.2f}s)")
        traceback.print_exc()
        result = e
    if typ == 0 and ark_main.has_after_finish_Thread:
        logger.system("开始执行完成线程指令。")
        ark_main.after_finish_Thread.start()
        if cover_result:
            result = ark_main.after_finish_Thread.get_result(True)
        ark_main.has_after_finish_Thread = False
    return result


def _check_request_with_stage(stagecode, request):
    try:
        if request in ItemStack().registItem(getDropList(stagecode)):
            return True
        return False
    except IndexError:
        logger.error(f"无法获得关卡'{stagecode}'所对应的掉落物，是否关卡名称错误？")
        return False


def _add_drop_to_list(drop_list, *itemStack):
    for item in drop_list:
        for stack in itemStack:
            if item["have"]:
                stack.addItem(item["name"], item["quantity"])
    return True


class ArkAutoRunner(object):
    def __init__(self,
                 adb_host=None,
                 gui_enabled=False,
                 with_commander=False):
        os.system("cls")
        ensure_adb_alive()
        self.Thread = Job()
        self.after_finish_Thread = Job()
        self.has_after_finish_Thread = False
        self.__adb_host = adb_host
        self.adb = ADBConnector(adb_serial=adb_host)
        self.root = Path(__file__).parent
        self.gui_enabled = gui_enabled
        self.gameTemp = GameTemplate("./imgReco/img/")
        RootData.set("gameTempGlobal", self.gameTemp)
        self.handler = mumu_handler.getSelectGameNow()
        self.getScreenShot = self.adb.screenshot
        self.reconizerC, self.reconizerE, self.reconizerN, self.reconizerN2 = getReconizer()
        self.time_sleep = time_sleep
        self.clicker = Clicker(self.adb)
        self.mapper = Mapping.Mapping("./ArkMapping/MapData2.dat")
        self.material_planner = MaterialPlanning()
        self.playerInfo = None
        self.in_attack = False
        self.total_itemStack = ItemStack()
        self.current_itemStack = ItemStack()
        self._force_stop = False
        self.mapData = ArkMap(self)
        self.dropLinker = ItemDropLinker()
        if with_commander:
            self.commander = commander()
            self.commandRegister(self.commander)
            self.commander.StartTrack()
        if self.handler[1] != -1:
            if self.handler[0][4] == 1280 and self.handler[0][5] == 809:
                logger.system("检测到Mumu模拟器，已开启快速图像采集")
                self.getScreenShot = getscreenshot
            else:
                logger.notice("检测到Mumu模拟器，请使用1280x720模式以开启快速图像采集！")

        # TODO:界面识别

    def run_after_current(self, lambda_funcing=None, cover=False):
        if lambda_funcing.__class__.__name__ != 'function':
            logger.error(f"function type must be 'function', got '{lambda_funcing.__class__.__name__}' instead")
            return False
        if self.has_after_finish_Thread and not cover:
            logger.error("当前已设定运行结束后任务,若想覆盖请使用cover=True")
            return False
        self.after_finish_Thread = Job(target=lambda_funcing)
        self.has_after_finish_Thread = True
        return True

    def reGetGame(self):
        mumu_handler.regetgame()
        self.handler = mumu_handler.getSelectGameNow()

    def kill_current_task(self):
        if self.Thread.is_running:
            # self.Thread.stop()
            stop_thread(self.Thread)
            logger.warning("已强制停止当前进程，清空进程信息。请检查当前页面状态。")
            self.Thread = Job()

    def stop_current_attack(self):
        if not self._force_stop:
            self._force_stop = True
            logger.notice("在本次进攻完成后将停止攻击")

    @staticmethod
    def _kill_adb():
        import psutil
        for pid in psutil.pids():
            if psutil.Process(pid).name() == 'adb.exe':
                try:
                    psutil.Process(pid).kill()
                except Exception as e:
                    logger.error(str(e))

    def restart_adb(self, kill=False):
        logger.notice("关闭adb中...", flush=False)
        try:
            del self.adb
        except AttributeError:
            pass
        if kill:
            self._kill_adb()
        logger.notice("关闭adb中...完成。正在重启adb")
        ensure_adb_alive()
        self.adb = ADBConnector(adb_serial=self.__adb_host)
        # mumu_handler.regetgame()
        self.reGetGame()
        if self.handler[1] != -1:
            if self.handler[0][4] == 1280 and self.handler[0][5] == 809:
                logger.system("检测到Mumu模拟器，已开启快速图像采集")
                self.getScreenShot = getscreenshot
            else:
                logger.notice("检测到Mumu模拟器，请使用1280x720模式以开启快速图像采集！")

    def resume_attack(self):
        if self._force_stop:
            self._force_stop = False
            logger.notice("已恢复进攻许可")

    def run_withThr(self, lambda_funcing=None):
        if lambda_funcing.__class__.__name__ != 'function':
            logger.error(f"function type must be 'function', got '{lambda_funcing.__class__.__name__}' instead")
            return False
        if self.Thread.is_running:
            logger.error("当前线程正在运行中，请等待执行完毕。")
            return False
        self.Thread = Job(target=lambda: ark_job_runnger(lambda_funcing, self, 0))
        logger.notice("线程开始运行")
        self.Thread.start()
        return True

    def _check_prts_type(self):
        prts_state = recognizePrtsStatus(self)
        if prts_state == 'DISABLE':
            self.adb.touch_tap((1140, 594), (10, 10))
            logger.notice("开启代理指挥")
            return True
        if prts_state == "LOCK":
            logger.error("代理指挥已锁定，是否已经使用自己的干员三星通关？")
            return False
        return True

    def logStageDrop(self, drop_list, atk_stage, atk_num, cost_time, log_drop=True, show_drop=True):
        end_items = recognizeEndItemsWithTag(self, drop_list)
        _add_drop_to_list(end_items, self.current_itemStack, self.total_itemStack)
        if show_drop:
            logger.common(formatDropItem(end_items))
        if log_drop:
            self._log_drop_item(end_items,
                                f'./logs/DROP_{time.strftime("%Y-%m-%d_%H_%M_%S")}_{atk_stage}_{atk_num}.jpg')
            self.dropLinker.writeStageDrop(atk_stage, end_items, cost_time)

    def attack_extermination(self, stage_set=None, max_atk=1,
                             use_ap_supply=False, use_diamond=False, use_thread=True,
                             log_drop=True):
        if use_thread:
            return self.run_withThr(
                lambda: self.attack_extermination(stage_set, max_atk, use_ap_supply, use_diamond, False, log_drop))

        def error(msg, err):
            logger.error(f"进攻剿灭作战'{stage_set}'失败[{msg}]:{err}")
            return False

        # 提示信息
        logger.warning('请保证在本剿灭作战中能够稳定400杀通关，否则在结束阶段将可能无法识别，需要人工手动介入！')
        # getStageSet
        if stage_set is None:
            stage_set = getStageTag().getStage('乌萨斯', '废弃矿区')  # TODO:每次轮换更新
        elif isinstance(stage_set, str):
            try:
                stage_set = getStageTag().getStage(None, stage_set)
            except ValueError as e:
                return error('无法获取关卡数据', e)
        if not isinstance(stage_set, StageInfo):
            return error('无法解析关卡数据', f'StageSet Typeof {type(stage_set)} cannot be parsed to StageInfo')
        # detect map
        if not self.mapData.fromMaptoMapMain():
            return error('无法跳转到地图界面', '当前界面无对应跳转方式')
        # check
        if not self.getLocation(self.getScreenShot(), ['map_main']):
            return error('跳转到地图界面失败', '可能存在通知等影响跳转。请检查！')
        # click into extre
        self.clicker.mouse_click(537, 662, t=2)
        # select position
        click_data = EXTER_CLICK_DATA.get(stage_set.getName())
        if click_data is None:
            return error('无效的地图名称', f"无效的地图名称:'{stage_set}'")
        for x, y in click_data:
            self.clicker.mouse_click(x, y, t=1.3)
        # start attack
        map_cost = stage_set.getCost()[0]  # ap_cost
        decide_atk = max_atk
        atk_stage = stage_set.getName()
        atk_num = 0
        self.current_itemStack = ItemStack()
        if not self._check_prts_type():
            return False
        inte_now, inte_max = recognizeBeforeOperationInte(self)
        self.playerInfo = PlayerConfig(int(inte_now), int(inte_max)) if self.playerInfo is None \
            else self.playerInfo.update(inte_now, inte_max)
        while self.playerInfo.startOperation(map_cost, use_diamond or use_ap_supply) \
                and max_atk != 0 and not self._force_stop:
            # 检测当前合成玉数量
            camp_num = recognizeCampaignNum(self)
            if camp_num['success']:
                camp_cur = camp_num['now']
                camp_lim = camp_num['max']
                logger.notice(f"当前合成玉数量为{camp_cur},最大合成玉获取数量为{camp_lim},还可获取{camp_lim - camp_cur}合成玉")
                if camp_lim - camp_cur < MIN_ENABLE_EXTER_ATK_CAMP_NUM:
                    logger.error(f"当前合成玉与最大合成玉获取上限小于最小可进攻设定值'{MIN_ENABLE_EXTER_ATK_CAMP_NUM}'，放弃攻击")
                    break
            else:
                return error('无效合成玉信息', '无法在当前页面获取合成玉信息，请检查当前位置！')
            max_atk -= 1
            atk_num += 1
            logger.common("当前实际理智(%s/%s),开始行动(第%s次/共%s次)。" % (inte_now, inte_max, atk_num, decide_atk))
            self.clicker.mouse_click(1148, 658)
            # if self.playerInfo.intellect + 1 < cost:
            max_atk, atk_num, uType = self._check_inte_using(inte_now, map_cost, max_atk, atk_num, use_ap_supply,
                                                             use_diamond)
            if uType is True:
                continue
            elif uType is False:
                break
            else:
                pass
            waitStartOperationAttack(self, lambda: self.clicker.mouse_click(1105, 521, at=0.3))
            start_time = time.time()
            time.sleep(12)
            # 循环检测当前剿灭作战信息
            while True:
                try:
                    kill_count = self.reconizerE.recognize2(imgops.crop_blackedge2(
                        Image.fromarray(self.getScreenShot(450, 20, 60, 21))), subset='0123456789/')[0]
                except:
                    kill_count = '-'
                reco_enermy = '-'
                try:
                    reco_enermy = self.reconizerE.recognize2(imgops.crop_blackedge2(
                        imgops.clear_background(Image.fromarray(cv2.split(self.getScreenShot(618, 20, 102, 21))[0]), 40)
                    ), subset='0123456789/')[0]
                    # enermy_num, total_enermy_num = reco_enermy.split('/', 1)
                except:
                    logger.warning(f"识别敌人数量出现错误(结果为{reco_enermy})")
                    # enermy_num, total_enermy_num = -1, -1
                try:
                    lo_count = self.reconizerE.recognize2(imgops.crop_blackedge2(
                        Image.fromarray(cv2.split(self.getScreenShot(837, 20, 26, 20))[2]), 120
                    ), subset='0123456789/')[0]
                except:
                    lo_count = '-'
                logger.notice(f"[ExtAssist]当前击杀数量:{kill_count:>3}|敌人数量:{reco_enermy:>7}|剩余防御点数:{lo_count:>2}")
                if waitExterminationEnd(self):
                    break
            cost_time = time.time() - start_time
            logger.notice(f"剿灭攻击结束！本次花费{cost_time:2f}秒")
            time.sleep(4)
            self.clicker.mouse_click(1209, 311, t=7)
            drop_list = {('AP_GAMEPLAY', '理智'), ('DIAMOND_SHD', '合成玉'), ('sprite_exp_card_t2', '初级作战记录'),
                         ("EXP_PLAYER", "声望"), ("GOLD", "龙门币")}
            self.logStageDrop(drop_list, atk_stage, atk_num, cost_time, log_drop)
            self.clicker.mouse_click(112, 150, t=5)
            self.playerInfo.endOperation()
            time.sleep(5)
        if max_atk != 0:
            logger.warning(f"已完成{atk_num}次,剩余{max_atk if max_atk > 0 else 'INFINITE'}次未攻击")
        self.playerInfo.stopOperation(-1)
        if self._force_stop:
            logger.warning('已强制停止！')
            self._force_stop = False
        logger.notice(f"[关卡数据统计]攻击{atk_stage} {atk_num}次,消耗"
                      f"{map_cost * atk_num}理智,获取掉落物:{self.current_itemStack.formatItems('%item%(%quantity%) ')}")
        return True

    def attack_planned(self, stage_set, use_thread=True, update_stage=False):
        if use_thread:
            return self.run_withThr(lambda: self.attack_planned(stage_set, False))
        if not isinstance(stage_set, (dict, StageSet)):
            logger.error("需要StageSet类型的stage_set")
            return False
        use_ap = stage_set.get('use_ap_supply', True)
        use_diam = stage_set.get('use_diamond', False)
        total_max_atk = stage_set.get('total_max_atk', -1)
        logger.notice(f"[计划攻击][全局攻击次数{'不限制' if total_max_atk == -1 else str(total_max_atk)}]"
                      f" 计划任务{str(stage_set.get('list', []))}")
        logger.notice(f"[计划攻击]{'不' if not use_ap else ''}使用理智药剂 {'不' if not use_diam else ''}使用源石恢复")
        stages = stage_set.get('stages', [])
        _CUR_STAGE = None
        _TAR_STAGE = None
        for index, stageName in enumerate(stage_set.get('list', [])):
            if stages[index]["stage"] != stageName:
                logger.error(f"关卡信息核对失败，请检查StageSet!(需要{stageName},得到了{stages[index]['stage']})")
                continue
            atkT = stages[index]["max_atk"]
            require = stages[index]['require'] if stages[index]['use_require'] else None
            _TAR_STAGE = stageName
            logger.notice(f"[计划攻击]开始攻击 关卡{_TAR_STAGE} "
                          f"{atkT if total_max_atk == -1 or atkT <= total_max_atk else total_max_atk}次 " +
                          f"需求列表为{str(stages[index]['require'])}" if stages[index]["use_require"] else f"无需求要求")
            at_stage = 0
            try:
                at_stage = 1
                assert self.mapData.changeStage(_CUR_STAGE, _TAR_STAGE)
                at_stage = 2
                assert self.attack_simple(_TAR_STAGE,
                                          atkT if total_max_atk == -1 or atkT <= total_max_atk else total_max_atk,
                                          require=require, use_ap_supply=use_ap, use_diamond=use_diam, use_thread=False)
                time_sleep(2)
                _CUR_STAGE = _TAR_STAGE
                continue
            except (Exception, AssertionError):
                logger.error(f"计划执行计划中关卡\'{stageName}\'失败：在{['准备', '切换地图', '自动攻击'][at_stage]}中：")
                traceback.print_exc()
                _CUR_STAGE = None

    def attack_simple_autolocate(self, stage, max_atk=-1,
                                 require=None,
                                 use_ap_supply=True,
                                 use_diamond=False,
                                 use_thread=True):
        if use_thread:
            return self.run_withThr(
                lambda: self.attack_simple_autolocate(stage, max_atk, require, use_ap_supply, use_diamond, False))
        step = '初始化'
        try:
            logger.notice(f"[自动定位]准备定位关卡{stage}...")
            step = '切换关卡'
            assert self.mapData.changeStage(None, stage)
            step = '进攻'
            assert self.attack_simple(stage, max_atk, require, use_ap_supply, use_diamond, False)
        except Exception as e:
            logger.error(f"执行自动化攻击出现错误：关卡{stage} 步骤:{step} 错误信息:{str(e)}")
            traceback.print_exc()
            return False
        return True

    def attack_simple(self, stage="AUTO",
                      max_atk=-1,
                      require=None,
                      use_ap_supply=True,
                      use_diamond=False,
                      use_thread=True,
                      planned_stage=None,
                      log_drop=True):
        if use_thread:
            return self.run_withThr(
                lambda: self.attack_simple(stage, max_atk, require, use_ap_supply, use_diamond, False))
        # 清空遗留的强制停止信息
        # self._force_stop = False
        # 对已指定的关卡进行自动攻击至无体力
        map_cost = getMapCost()
        atk_stage = stage
        RETURN_VALUE = True
        # _LOC = self.getLocation(ranges=ArkMap.RECO)
        # if 'map_atk' not in _LOC:
        if not self.gameTemp.dingwei("on_atk_beg\\start.png", self.getScreenShot(1102, 624, 150, 66)):
            logger.error("当前未在关卡选择内，无法使用简单模式进行挂机！")
            logger.error("请切换到关卡内(能够直接点击开始行动)并重启程序")
            return False

        if stage == "AUTO":
            # 使用tesseract检测关卡最优
            rec = recognizeOperation(Image.fromarray(self.getScreenShot(881, 81, 86, 34)), map_cost)
            # rec = self._check_ocr_until_success(881, 81, 86, 35, map_cost)
            if rec[0]:
                logger.common("检测到当前关卡:%s 消耗%s" % (rec[0], rec[1].replace("ap_", "理智:").replace("et_", "门票:")))
                atk_stage = rec[0]
            else:
                logger.error("请使用stage='STAGE_CODE'进行手动设置！")
                return False
        else:
            rec = [stage, map_cost.where(stage)]
            if rec[1] is None:
                logger.error("未找到当前关卡%s所对应的体力消耗，程序版本是否过时？" % stage)
                return False
            logger.notice("设定当前关卡:%s 消耗%s" % (stage, rec[1].replace("ap_", "理智:").replace("et_", "门票:")))
        ap_text = rec[1].split("_")[0].replace("ap", "理智").replace("et", "门票")
        if ap_text == "门票":
            use_diamond, use_ap_supply = False, False
        cost = int(rec[1].split("_")[1])
        # 检测理智用reconizer
        request_require = False
        if require is not None:
            request_require = True
            if not _check_request_with_stage(atk_stage, require):
                logger.error('检测掉落物与需求不匹配！请检查')
                return False

        now, max_ = self.reconizerC.recognize2(Image.fromarray(self.getScreenShot(1120, 20, 130, 40)),
                                               subset="1234567890/")[0].split("/")
        if int(now) < cost and (not use_ap_supply and not use_diamond):
            logger.error("当前%s(%s)小于关卡消耗%s，已停止" % (ap_text, ap_text, now))
            return False
        self.playerInfo = PlayerConfig(int(now), int(max_)) if self.playerInfo is None else self.playerInfo.update(now,
                                                                                                                   max_)
        delay_time = 25
        decide_atk = max_atk if max_atk != -1 else "AUTO"
        atk_num = 0
        # 检查代理指挥
        if not self._check_prts_type():
            return False
        self.current_itemStack = ItemStack().registItem(getDropList(atk_stage), 0)
        while self.playerInfo.startOperation(cost,
                                             use_diamond or use_ap_supply) and max_atk != 0 and not self._force_stop:
            max_atk -= 1
            atk_num += 1
            now, max_ = recognizeBeforeOperationInte(self)
            if request_require:
                logger.debug("Require List:" + require.formatItems("%item%(%quantity%) "))
                logger.debug("Get:" + self.current_itemStack.formatItems("%item%(%quantity%) "))
                if require <= self.current_itemStack:
                    max_atk = 0
                    break
            logger.common("当前实际%s(%s/%s),预测%s(%s),开始行动(第%s次/共%s次)。" % (
                ap_text, now, max_, ap_text, self.playerInfo.intellect + 1, atk_num, decide_atk))
            self.clicker.mouse_click(1148, 658)
            max_atk, atk_num, uType = self._check_inte_using(now, cost, max_atk, atk_num, use_ap_supply,
                                                             use_diamond)
            if uType is True:
                continue
            elif uType is False:
                break
            waitStartOperationAttack(self, lambda: self.clicker.mouse_click(1105, 521, at=0.3))
            start_time = time.time()
            # 检查结束
            time.sleep(delay_time)
            # TODO:检查结束的时候还应该检查是否失败
            logger.debug("等待结束，开始检测通关信息。")
            while not self.getLocation(getscreenshot(99, 577, 427, 116), "atk_end", sub_area=[99, 577, 427, 116]):
                time.sleep(1)
                if self.gameTemp.dingwei("on_atk_end\\lvl_up.png", self.getScreenShot(657, 328, 50, 50)):
                    time.sleep(4)
                    logger.notice("您已升级！")
                    self.playerInfo.restore()
                    self.adb.touch_tap((931, 278), (15, 15))
            cost_time = time.time() - start_time
            logger.common("行动结束,本次花费%.2f秒" % cost_time)
            delay_time = cost_time - 9
            time.sleep(7)
            self.logStageDrop(atk_stage, atk_stage, atk_num, cost_time, log_drop)
            self.adb.touch_tap((796, 466), (15, 15))
            time.sleep(1)
            self.adb.touch_tap((796, 466), (15, 15))
            time.sleep(3)
            self.playerInfo.endOperation()
        if max_atk != 0:
            logger.warning(f"已完成{atk_num}次,剩余{max_atk if max_atk > 0 else 'INFINITE'}次未攻击")
        if planned_stage is not None:
            planned_stage.delStage(atk_stage, atk_num)
        self.playerInfo.stopOperation(-1)
        if self._force_stop:
            logger.warning("已强制停止！")
            self._force_stop = False
        logger.notice(f"[关卡数据统计]攻击{stage if stage != 'AUTO' else rec[0] + '(自动识别)'} {atk_num}次,消耗"
                      f"{cost * atk_num}{ap_text},获取掉落物:{self.current_itemStack.formatItems('%item%(%quantity%) ')}")
        return RETURN_VALUE

    def attackOnce(self, stage=None):
        if stage is None:
            return self.attack_simple(max_atk=1)
        else:
            return self.attack_simple_autolocate(stage, max_atk=1)

    def planRecruit(self, force=0, use_thread=True):
        if use_thread:
            return self.run_withThr(lambda: self.planRecruit(force, False))
        # 先检查当前所处位置，是否是在选择Tag中或公开招募界面
        if not self.mapData.toMain():
            return logger.error('无法返回主界面！')
        if self.getLocation(ranges=["main"]):
            self.clicker.mouse_click(1003, 510, t=1.2)
        assert self.mapper.locateImage(getscreenshot(), 'recruit')
        try:
            recruit_detail = getRecruitDetail(self)
            for _ in recruit_detail:
                logger.debug(str(_))
            for _ in recruit_detail:
                if _["type"] == 'FINISH':
                    _['can'] = True
                    x, y = _['centre']
                    sel_tag = self.getScreenShot(x - 192, y - 65, 192 * 2, 65 - 8)  # +-192 ->x,-8~-65->y

                    y += 77
                    self.clicker.mouse_click(x, y, t=0.7)
                    waitGachaSkipBtn(self)
                    time_sleep(2.3)
                    self.clicker.mouse_click(1220, 45)
                    time_sleep(3)
                    ge_im = self.getScreenShot()
                    ge_im[20:20 + sel_tag.shape[0], 40:40 + sel_tag.shape[1]] = sel_tag
                    del sel_tag
                    cv2.imwrite(f'./logs/RECRUIT_{time.strftime("%Y-%m-%d_%H_%M_%S")}_{str(_["id"])}.jpg', ge_im,
                                [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    self.clicker.mouse_click(1236, 147, t=1.3)
                if _["can"]:
                    logger.common("选择第%d个公招,当前force=%d" % (_["id"] + 1, force))
                    x, y = _["centre"]
                    self.clicker.mouse_click(x, y, t=1)
                    plan_, rec_ = self.planRecruitSingle(force=force > 0)
                    if plan_["decision"]["action"] == 'refresh':
                        waitRecruitRefreshSuccess(self)
                        time_sleep(1)
                        plan_, rec_ = self.planRecruitSingle(select=False)
                        if plan_['decision']['action'] == 'choose':
                            self._select_recruit_tag(plan_["decision"])
                        elif force > 0:
                            logger.notice("强制选择：空项目")
                            self._select_recruit_tag({"action": "choose", "tag": [], "time": (9, 0)})
                            plan_['decision']['action'] = "choose"
                        elif plan_['decision']['action'] == 'exit':
                            self.clicker.mouse_click(978, 647, t=1, at=1)  # back
                    force -= 1
                    if plan_['decision']['action'] not in ["choose", "exit"]:
                        self.clicker.mouse_click(978, 647, t=1, at=1)
                time_sleep(1.5)
            self.clicker.mouse_click(72, 40, t=1.5, at=1.4)
        except Exception as e:
            logger.error("出现错误，强制返回主页")
            logger.error("Error:%s" % str(e))
            self.clicker.mouse_click(271, 38, t=1)
            self.clicker.mouse_click(93, 173, t=3)

    def planRecruitSingle(self, taglist=None, can_refresh=False, select=True, force=False):
        # 检查当前所处位置
        if taglist is None:
            reco_tags = recognizeRecruit(self)
            if None in reco_tags["tags"]:
                logger.error("识别的标签中存在无法识别项，请手动选择！")
                logger.debug("标签：%s" % str(reco_tags))
                return None, reco_tags
            can_refresh = reco_tags["can_refresh"]
        else:
            reco_tags = {"tags": taglist,
                         "recoV": None,
                         "can_refresh": can_refresh,
                         "cost": 0}
        logger.common("获取标签:" + str(reco_tags["tags"]) + "用时%.3f秒" % reco_tags["cost"])
        result = planRecruit(reco_tags["tags"], can_refresh)
        if result["decision"]["action"] == "exit":
            logger.common("建议跳过本次公开招募")
        elif result["decision"]["action"] == 'refresh':
            logger.common("建议刷新本次公开招募")
        else:
            decision = result["decision"]
            logger.common("建议进行招募：选择TagIndex:" + str(decision["tag"]) +
                          "时间:%sH%sM" % (decision["time"][0], decision["time"][1]))
        if select:
            result['decision'] = self._select_recruit_tag(result["decision"], force)
        return result, reco_tags

    def _select_recruit_tag(self, decision, force=False):
        if decision["action"] == "exit":
            if force:
                decision = {'action': 'choose', 'time': (9, 0), 'tag': []}
            else:
                self.clicker.mouse_click(979, 648)
                return decision
        if decision["action"] == 'refresh':
            self.clicker.mouse_click(970, 408, t=0.7)
            self.clicker.mouse_click(841, 507)
            return decision
        if decision["action"] == "choose":
            # 检查是否成功(防止出现龙门币不足的情况)
            for index in decision["tag"]:
                x, y = [(448, 384), (616, 384), (782, 384), (448, 456), (616, 456)][index]
                self.clicker.mouse_click(x, y)
            for _ in range(decision["time"][0] - 1):
                self.clicker.mouse_click(452, 150)
            for _ in range(decision["time"][1] - 1):
                self.clicker.mouse_click(618, 150)
            _LM, _RE, _AL = recognizeCanRecruit(self)
            if _AL:
                self.clicker.mouse_click(974, 582, t=1)
            else:
                logger.error(f"当前{'' if _LM else '龙门币'}{'和' if not _LM and not _RE else ''}"
                             f"{'' if _LM else '公开招募券'}不足，无法招募，返回。")
                self.clicker.mouse_click(979, 648)
            return decision

    def _clear_task_reward(self):
        while self.gameTemp.dingwei("main\\task\\take.png", getscreenshot(1012, 131, 95, 27), 0.1) and not \
                self.gameTemp.dingwei("main\\task\\finish.png", getscreenshot(95, 157, 74, 33), 0.9):
            self.clicker.mouse_click(1118, 146, rx=(-25, 25))
            self.clicker.mouse_click(1115, 147, rx=(-25, 25), t=0.5)
        self.clicker.mouse_click(66, 171, t=0.6)
        self.clicker.mouse_click(66, 171, t=0.3)
        if self.gameTemp.dingwei("main\\task\\take.png", getscreenshot(1012, 131, 95, 27), 0.4) and not \
                self.gameTemp.dingwei("main\\task\\finish.png", getscreenshot(95, 157, 74, 33), 0.9):
            self._clear_task_reward()
        return True
        # self.clicker.mouse_click(1077, 138, t=0.1)
        # self.clicker.mouse_click(1077, 138, t=0.1)

    def check_to_main_notice(self):
        # 先检查通知事件(检查是否每日新登录)
        # 检查每日签到事件
        # 检查特殊事件（如登录活动etc)
        pass

    def clear_daily_task(self, back_to_main=True, use_thread=True):
        if use_thread:
            return self.run_withThr(lambda: self.clear_daily_task(back_to_main, False))
        time_sleep(1.2)
        if not self.mapData.toMain():
            logger.error('无法返回到主界面！')
            return False
        if self.mapper.locateImage(getscreenshot(), 'main', method=3):
            self.clicker.mouse_click(805, 606, t=1.5)
        if self.mapper.locateImage(getscreenshot(), ["task", "task_newbee"], method=3)[0] == "task_newbee":
            self.clicker.mouse_click(768, 36, t=0.8)
            self._clear_task_reward()
            logger.notice(f"日常任务剩余识别：{recognizeTaskLeft(self)}")
            self.clicker.mouse_click(968, 36, t=0.8)
            self._clear_task_reward()
            logger.notice(f"周常任务剩余识别：{recognizeTaskLeft(self)}")

        else:
            self._clear_task_reward()
            logger.notice(f"日常任务剩余识别：{recognizeTaskLeft(self)}")
            self.clicker.mouse_click(865, 37, t=0.8)
            self._clear_task_reward()
            logger.notice(f"周常任务剩余识别：{recognizeTaskLeft(self)}")
        if back_to_main:
            self.clicker.mouse_click(91, 39, t=0.7)

    def _filter_item_planner_unreachable(self, stack: ItemStack):
        for k, v in list(stack.items()):
            if self.material_planner.item_name_to_id.get('zh').get(k, None) is None or "芯片" in k:
                logger.warning(f"filter {k} in ItemStack:Item not exist in planner.")
                stack.pop(k)
        logger.debug("after filter:" + stack.formatItems('%item%(%quantity%) '))
        return stack

    def planMaterial(self, required_dct, owned_dct=None):
        owned_dct = owned_dct or {}
        ret = self.material_planner.get_plan(self._filter_item_planner_unreachable(required_dct),
                                             owned_dct, print_output=False, outcome=True,
                                             gold_demand=True, exp_demand=True, store=True, server='CN')
        return ret

    def updatePlannerData(self):
        try:
            self.material_planner.update(force=True)
            logger.system("已完成Planner的数据更新！")
        except Exception as e:
            logger.error("Planner数据更新出现错误：%s" % e)

    def clear_mail_item(self):
        if not self.getLocation(ranges='main'):
            logger.error("请切换到主界面(main)运行邮件收取！")
            return False
        if (self.getScreenShot()[25][217] == [1, 104, 255]).all():
            self.clicker.mouse_click(194, 43, t=1.5)
            waitCustomImageDetect(self, "main\\receive_all_mail.png", [1056, 644, 171, 44], delay=8)
            time_sleep(1.4)

            logger.notice(f"收取邮件[当前邮件"
                          f"{self.reconizerN.recognize(imgops.clear_background(getscreenshot(98, 641, 101, 28), 100))}]"
                          f"[{self.reconizerN.recognize(imgops.clear_background(getscreenshot(307, 638, 35, 32), 100))}"
                          f"封未读邮件]")
            # reconizerN.recognize(imgops.clear_background(getscreenshot(98, 641, 101, 28), 100)) -> 邮件统计
            # reconizerN.recognize(imgops.clear_background(getscreenshot(307,638,35,32),100)) ->未读邮件
            self.clicker.mouse_click(1143, 664, t=2)
            waitCustomImageDetect(self, "main\\recv_mail_g.png", [586, 138, 113, 39], threshold=0.93)
            self.clicker.mouse_click(1143, 664, t=2)
        return True

    def clear_credit_item(self, use_thread=True):
        if use_thread:
            return self.run_withThr(lambda: self.clear_credit_item(False))
        # TODO:改用wait->image方式提升效率
        # assert self.mapper.locateImage(getscreenshot(), 'main', method=3), "请在主界面(main)运行本指令！"
        self.mapData.toMain()
        getMapCost()
        self.clicker.mouse_click(365, 575, t=1.5)
        self.clicker.mouse_click(125, 228, t=1)
        waitCustomImageDetect(self, "friends\\visit.png", (946, 168, 106, 40), delay=10)
        self.clicker.mouse_click(1000, 166, t=1.5)
        for _ in range(11):
            waitVisitNextFriend(self, lambda: self.clicker.mouse_click(1200, 634, at=1, t=3))
        self.clicker.mouse_click(271, 36, t=1.1)
        self.clicker.mouse_click(1200, 172, t=1.4)
        self.clicker.mouse_click(1205, 104, t=2)
        self.clicker.mouse_click(1021, 41, t=2)
        self.clicker.mouse_click(1021, 41, t=1.2)
        if self.gameTemp.dingwei("shop\\credit_use.png", self.getScreenShot(581, 151, 115, 29)):
            self.clicker.mouse_click(1205, 104, t=0.5)
        for _ in range(10):
            x = 132 + (253 * (_ % 5))
            y = 274 + (254 * (_ // 5))
            # check out of stack
            if self.gameTemp.dingwei('shop\\credit_oos.png', getscreenshot(x - 104, y + 10, 34, 24)):
                logger.error(f"第{_ + 1}件信用商品已售罄！")
                continue
            self.clicker.mouse_click(x, y, rx=(-30, 30), ry=(-30, 30), t=0.3)
            logger.common(f"购买第{_ + 1}件信用商品")
            waitCustomImageDetect(self, 'shop\\credit_buy.png', [838, 565, 44, 35],
                                  lambda: self.clicker.mouse_click(935, 579, at=0.3, t=1.3), 1.2)
            if waitGetCreditItemOrNot(self) is False:
                logger.common("信用点不足，无法购买，退出")
                self.clicker.mouse_click(1205, 104, t=0.7)
                break
            self.clicker.mouse_click(908, 39, t=1.3)
        logger.notice("已完成信用商店购买，返回主页")
        self.clicker.mouse_click(271, 38, t=1)
        self.clicker.mouse_click(93, 173, t=3)

    def _exit(self):
        logger.system("ArkAutotools Shutting down...")
        if self.playerInfo is not None:
            self.playerInfo.stop()
        self.mapper.writeMapping()
        # self.mapData._writeSetting()
        logger.log2file("./logs/" + getLogFileName())
        try:
            del self.adb
        except (NameError, AttributeError):
            pass
        logger.system("Bye~")
        sys.exit(0)
        # self.commander.StopTrack()

    def exit(self):
        self._exit()

    def quit(self):
        self._exit()

    @RootData.cache("ArkFont-NSH_Demi")
    def _get_font_NSHDemi(self, size=14):
        from PIL import ImageFont
        return ImageFont.truetype("./font/" + 'NotoSansHans-DemiLight.otf', size, encoding='utf-8')

    def _putText(self, image, x, y, strs, fontsize=20, font=None, color=None):
        from PIL import ImageDraw
        cv2img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pilimg = Image.fromarray(cv2img)
        draw = ImageDraw.Draw(pilimg)  # 图片上打印
        font = font or self._get_font_NSHDemi(fontsize)
        color = color or (255, 255, 255)
        draw.text((x, y), strs, color, font=font)
        # 参数1：打印坐标，参数2：文本，参数3：字体颜色，参数4：字体
        return cv2.cvtColor(np.array(pilimg), cv2.COLOR_RGB2BGR)

    def _log_drop_item(self, drop_list, savepath):

        image = getscreenshot(0, 441, 1280, 720 - 441).astype(np.uint8)
        for _ in drop_list:
            if not _["have"]:
                continue
            x, y = _["_pos"]
            image = self._putText(image, x + 427, y + 117, f'{_["name"]}:{str(_["quantity"])}')
        cv2.imwrite(savepath, image, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

    def commandRegister(self, cmder):
        cmder.createExitCommand("exit", "quit", function=self._exit, help="退出程序")
        cmder.createCommand('ark_main', function=self.commandlistener, help="Ark指令")

    def _show_commander_help(self):
        logger.help(f"ArkAutoRunner Version{VERSION} Running on {sys.platform}")
        logger.help("")
        logger.help("ark_main [-h/help]                             -获取ArkAutoRunner的帮助")
        # logger.help("ark_main [-a/attack] [s/l]                     -以单关攻击(s)/列表攻击(l)开始关卡")
        # logger.help("ark_main [-l/list] <ListofStage:(str:int)>     -在列表攻击模式下选择攻击的关卡")
        # logger.help("   e.g. ark_main -a l -l 1-7:5 CE-5:4")
        # logger.help("ark_main [-t/times] <MaxAttackTimes:int>       -在单关攻击模式下最大进攻次数")
        # logger.help("ark_main [-r/require] <Require>                -附加需求的掉落物品(会受到次数限制)")
        # logger.help("   e.g. ark_main -a s -r 聚酸酯组:1 扭转醇:1")
        # logger.help("ark_main [-p/plan] -r <Require> -o <Owned>     -规划")
        # logger.help("ark_main                          -                                   ")
        logger.help("=*=*=*=*=*=*=*=*=*=*=*=ArkAutoRunner Help=*=*=*=*=*=*=*=*=*=*=*=")
        logger.error("正在施工中...")

    def autoUpdate(self, use_thread=True):
        if use_thread:
            return self.run_withThr(lambda: self.autoUpdate(False))
        from ArkTagData.GitUpdater import updateGameData
        # Update GameData
        updateGameData()
        # reset all cache
        RootData.clearCache()
        # catch image from prts.wiki etc
        from ArkTagData.DataUpdater import updateItemData, updateRecruitTag
        updateRecruitTag()
        updateItemData()
        return True

    def commandlistener(self, *cmd):
        # print(cmd)
        if not cmd:
            self._show_commander_help()
            return 0
        commands = cmd[0]

    def getLocation(self, image=None, ranges=None, group=None, method=3, sub_area=None, addon=False, showdebug=False):
        image = image if image is not None else self.getScreenShot()
        return self.mapper.locateImage(image, ranges=ranges, group=group, method=method, sub_area=sub_area, addon=addon,
                                       show_debug=showdebug)

    def sleep_computer_after_current_atk(self):
        self.run_after_current(lambda: os.system("shutdown -h"))
        return True

    def getDropInfoHistory(self, stage: str, timerange: list = None, filter: list = None):
        class mainDropInfo:
            def __init__(self):
                self.param = []
                self.value = []
                self.num = 0

            def add(self, stack):
                self.num += 1
                if stack in self.param:
                    self.value[self.param.index(stack)] += 1
                    return True
                self.param.append(stack)
                self.value.append(1)

            def __bool__(self):
                return bool(self.param)

        ret = self.dropLinker.getStageDrop(stage)
        itemStack = ItemStack()
        mainDropInfo = mainDropInfo()
        for info in ret:
            itemStack = itemStack + info.dropList
            items = ItemStack().addItemFromList_NameQuantity(info.getByType(2))
            mainDropInfo.add(items)
        ttl = len(ret)
        extraInfo = {}
        for type_, id_ in getStageTag().getStage(stage).getDropInfo().getDropList():
            name = getItemTag()['items'].get(id_)['name']
            if 2 <= type_ <= 3:
                extraInfo.setdefault(name, ' 主要掉落' if type_ == 2 else ' 特殊掉落')

        def proc_percent(val):
            if val >= 5.0 or val <= 0:
                if int(val) == val:
                    return str(int(val))
                return str(val)
            return f"{round(val * 100, 2)}%"

        def log(s):
            logger.notice(f"[DropInfoHistory] {s}")

        def replacer(mapcost: str):
            try:
                return mapcost.replace('_', ':').replace('ap', '理智').replace('et', '门票')
            except:
                return None

        def fill_chi_char(str_, len_=30):
            chr_len = 0
            for char_ in str_:
                if ord(char_) < 128:
                    chr_len += 1
                else:
                    chr_len += 2
            need = len_ - chr_len
            return str_ + ' ' * (need if need >= 0 else 0)

        sspend = replacer(getMapCost().where(stage))
        sspend_value = int(sspend.split(':')[1])
        log(f"关卡{stage}物品掉落信息 总{ttl}次攻击被统计 单次攻击消耗{sspend}")
        log(f"物品名称        | 数量   | 平均概率  | 期望理智 | 附加信息")
        for item, value in itemStack.items():
            expect = proc_percent(round(value / ttl, 2))
            log(
                f"{item.ljust(9, chr(12288))}| {fill_chi_char(str(value), 6)}"
                f"| {expect:8}"
                f"| {round(sspend_value / (value / ttl), 2):7} "
                f"|{extraInfo.get(item, '')}")
        log('-' * 51)
        if mainDropInfo:
            log(f"[MainDrop][I] {fill_chi_char('主要掉落物内容', 20)} |  次数  |  比例")
            for ind, stack in enumerate(mainDropInfo.param):
                cur_times = mainDropInfo.value[ind]
                log(f"[MainDrop][{ind:1}] {fill_chi_char(str(stack), 18)} | {cur_times:6d} | "
                    f"{proc_percent(cur_times / mainDropInfo.num)}")

    def _check_inte_using(self, now, cost, max_atk, atk_num, use_ap_supply, use_diamond):
        if int(now) < cost:
            self.time_sleep(0.5)
            if self.gameTemp.dingwei("on_atk_beg\\use_ap_recov.png",
                                     self.getScreenShot(691, 80, 73, 46)) and use_ap_supply:
                logger.common("使用理智药剂恢复理智")
                self.clicker.mouse_click(1090, 579)
                self.time_sleep(0.5)
                if waitApRecovery(self):
                    now = recognizeBeforeOperationInte(self)[0]
                    logger.common("理智已成功恢复至%s" % now)
                    self.playerInfo.update(now)
                    max_atk += 1
                    atk_num -= 1
                return max_atk, atk_num, True
            elif self.gameTemp.dingwei("on_atk_beg\\use_diam_recov.png",
                                       self.getScreenShot(1005, 84, 67, 41)) and use_diamond:
                logger.common("使用源石恢复理智")
                self.clicker.mouse_click(1090, 579)
                if waitApRecovery(self):
                    now = recognizeBeforeOperationInte(self)[0]
                    logger.common("理智已成功恢复至%s" % now)
                    self.playerInfo.update(now)
                    max_atk += 1
                    atk_num -= 1
                return max_atk, atk_num, True  # TODO:做一下碎石恢复
            else:
                max_atk += 1
                atk_num -= 1
                RETURN_VALUE = False
                logger.warning("理智不足且无法自动回复。")
                return max_atk, atk_num, False
        return max_atk, atk_num, None


if __name__ == '__main__':
    import os
    import cv2
    from utils.logger import get_cur_info


    def saveImage(image, path=".\\imgReco\\img\\saver.png"):
        cv2.imwrite(path, image)


    def showImage(image):
        cv2.imshow('debug', image)
        cv2.waitKey(0)


    def _randstr(len_=8):
        import random
        import string
        r = ''
        for _ in range(len_):
            r += random.choice(string.ascii_letters + '0123456789' + '-_')
        return r


    def activitySave(name, pos=0):
        # 100x36
        if pos == 0:
            img = getscreenshot(790, 633, 100, 36)
        elif pos == 1:
            img = getscreenshot(944, 633, 100, 36)
        else:
            logger.error(f'还未设定位于{pos}的抓取参数！')
            return
        cv2.imwrite(fr".\imgReco\img\main\map\a_{name}.png", img)
        return True


    def mapSave(save=False, path='stagesig'):
        img = getscreenshot()
        dli_r = ark.gameTemp.dingwei("main\\map\\stagesig\\_operation.png", img, 0.8) + ark.gameTemp.dingwei(
            "main\\map\\stagesig\\_tutorial.png", img, 0.7) + \
                ark.gameTemp.dingwei("main\\map\\stagesig\\_operation_w.png", img, 0.8)
        logger.debug(dli_r)
        if len(dli_r) == 1:
            dli = dli_r
        else:
            dli = []
            for ind in range(len(dli_r) - 1):
                x, y = dli_r[ind]
                x_, y_ = dli_r[ind + 1]
                if abs(x - x_) < 3 and abs(y - y_) < 3:
                    continue
                dli.append((x, y))
        for ind, _ in enumerate(dli):
            x, y = _
            # showImage(np.asarray(imgops.clear_background(Image.fromarray(img[y + 11:y + 40, x:x + 72]))))
            # recov = ark_main.reconizerC.recognize(
            #     imgops.clear_background(Image.fromarray(img[y + 11:y + 40, x:x + 72]), 100))
            recov = ['']
            rstr = _randstr(16)
            print(f'Find Operation/Tutorial {recov[0]} at ({x},{y}) named {rstr}')
            # idata = recov[0]
            if save:
                # cv2.imwrite(r".\imgReco\img\main\map\ep\\" + rstr + ".png", img[y:y + 40, x:x + 72])
                cv2.imwrite(f".\\imgReco\\img\\main\\map\\{path}\\{rstr}.png", img[y + 11:y + 40, x:x + 72])


    logger.warning("Please DO NOT directly use this file to run except in debug mode")
    logger.warning("use \"from {} import ArkAutoRunner\" instead".format(os.path.basename(__file__)[:-3]))
    try:
        get_cur_info(2)  # In ide like pycharm it won't have any problem,but in cmd it can take error
        logger.warning("ark_main Commander work WRONGLY in Pycharm,disabled")
        ark = ArkAutoRunner()
    except:
        logger.setDebug(False)
        ark = ArkAutoRunner(with_commander=True)

    dailyStage = StageSet().use_ap_supply(False).addStage('1-7', 7).addStage('6-11', 10)
