from config.RootData import RootData
from utils.logger import root_logger as logger
import struct
import sys
import os
import time

RootData.set("Config_version", 1.1)


# 结构体-脚本前置
class Structure(object):
    def __init__(self, data=None, Magic=None, file=None):
        self._filename = None
        self._fileopen = False
        if Magic:
            self.magic = Magic
        if data:
            self.data = data
        if file:
            self.readFile(file)

    def readFile(self, filename):
        if not os.path.exists(filename):
            logger.warning("%s不存在,自动创建！" % filename)
            fn = '.\\' + filename
            f = open(fn, 'w')
            f.write('')
            f.close()
        self._filename = filename
        self.data = open(filename, 'rb')
        self._fileopen = True

    def readData(self, num=0):
        return self.data.read(num)

    def checkHeader(self):
        if self.magic and self.data:
            p = self.data.tell()
            self.data.seek(0)
            if list(self.data.read(len(list(self.magic)))) == list(self.magic.encode()):
                # self.data.seek(p)
                return True
            else:
                # self.data.seek(p)
                return False
        elif self.magic == None:
            return True
        else:
            return False


# 目录树状结构-脚本前置
class configTree(object):
    def __init__(self, root='.', importdata=None):
        self._root = root
        self.item = []
        self.folder = []
        self.wrong = None
        if importdata:
            self.import_from_data(importdata)

    def _imp_data_list_inner(self, listdata, folder):
        for item_index in range(len(listdata)):
            item = listdata[item_index]

            if type(item) == dict:
                folder.addChild(str(item_index))
                self._imp_data_dict_inner(item, getattr(folder, str(item_index)))
            elif type(item) == list:
                folder.addChild(str(item_index))
                self._imp_data_list_inner(item, getattr(folder, str(item_index)))
            else:
                folder.set(str(listdata.index(item)), item)

    def _imp_data_list(self, listdata):
        for item_index in range(len(listdata)):
            item = listdata[item_index]
            if type(item) == dict:
                self.addChild(str(item_index))
                self._imp_data_dict_inner(item, getattr(self, str(item_index)))
            elif type(item) == list:
                self.addChild(str(item_index))
                self._imp_data_list_inner(item, getattr(self, str(item_index)))
            else:
                self.set(str(item_index), item)

    def _imp_data_dict_inner(self, dictdata, folder):
        for item in dictdata.keys():
            if type(dictdata.get(item)) == dict:
                folder.addChild(str(item))
                self._imp_data_dict_inner(dictdata.get(item), getattr(folder, str(item)))
            elif type(dictdata.get(item)) == list:
                folder.addChild(str(item))
                self._imp_data_list_inner(dictdata.get(item), getattr(folder, str(item)))
            else:
                folder.set(str(item), dictdata.get(item))

    def _imp_data_dict(self, dictdata):
        for item in dictdata.keys():
            if type(dictdata.get(item)) == dict:
                self.addChild(str(item))
                self._imp_data_dict_inner(dictdata.get(item), getattr(self, str(item)))
            elif type(dictdata.get(item)) == list:
                self.addChild(str(dictdata.index(item)))
                self._imp_data_list_inner(dictdata.get(item), getattr(self, str(dictdata.index(item))))
            else:
                self.set(str(item), dictdata.get(item))

    def import_from_data(self, datain):
        if type(datain) == dict:
            self._imp_data_dict(datain)
        elif type(datain) == list:
            self._imp_data_list(datain)
        else:
            logger.error('数据非list/dict形！')

    def delChild(self, name):
        return self.remove(name)

    def remove(self, name):
        if hasattr(self, name):
            if name in self.item:
                self.item.pop(self.item.index(name))
                setattr(self, name, None)
                return True, 'item'
            elif name in self.folder:
                self.folder.pop(self.folder.index(name))
                setattr(self, name, None)
                return True, 'folder'
            else:
                setattr(self, name, None)
                return True, None
        else:
            return False, None

    def set(self, name=None, value=None, remove=False):
        setattr(self, name, value)
        if name not in self.item:
            self.item.append(name)
            return True
        elif remove:
            setattr(self, name, value)
            self.item.pop(self.item.index(name))
            return True
        else:
            setattr(self, name, value)
            return True

    def get(self, name=None):
        if hasattr(self, name):
            return getattr(self, name)
        else:
            return None

    def check(self, name=None):
        return hasattr(self, name)

    def copyItem(self, i_from='', i_to=''):
        if self.check(i_from):
            self.set(i_to, self.get(i_from))
            return True
        else:
            logger.error('不存在名为%s的数据') % i_from
            return False

    def _copy_inner(self, cfg_from, folder_name):
        New_cfg = configTree(root=folder_name)
        for item in getattr(cfg_from, folder_name).item:
            New_cfg.set(item, getattr(cfg_from, folder_name).get(item))
        for folder in getattr(cfg_from, folder_name).folder:
            r = self._copy_inner(getattr(cfg_from, folder_name), folder)
            New_cfg.addChild(data=r)
        return New_cfg

    def copyFolder(self, n_from='', n_to=''):
        if self.check(n_from):
            if not self.check(n_to):
                self.addChild(n_to)
                for item in getattr(self, n_from).item:
                    getattr(self, n_to).set(item, getattr(getattr(self, n_from), item))
                for folder in getattr(self, n_from).folder:
                    data = self._copy_inner(getattr(self, n_from), folder)
                    getattr(self, n_to).addChild(data=data)
            else:
                logger.error('%s的子数组已存在')
                return False
        else:
            logger.error('不存在名为%s的子数组')
            return False

    def listall(self):
        try:
            logger.common('[item]' + str(self.item)[1:-1:])
            print('[folder]' + str(self.folder)[1:-1:])
            return True
        except:
            logger.error("不存在参数！")
            return False

    def addChild(self, name=None, data=None):
        if name:
            if not hasattr(self, name):
                setattr(self, name, configTree(name))
                self.folder.append(name)
                return True
            elif getattr(self, name) == None:
                setattr(self, name, configTree(name))
                self.folder.append(name)
                return True
            elif name in self.folder:
                logger.error("子分支名称重复了")
                return False
            else:
                logger.error('禁止使用子数组名称命名')
                return False
        elif data:
            if hasattr(data, '_root'):
                if data._root not in self.folder:
                    self.folder.append(data._root)
                    setattr(self, data._root, data)
                    return True
                else:
                    logger.error("子分支名称重复了")
                    return False
            else:
                logger.error('分支数据错误')
                self.wrong = data
                return False
        else:
            logger.error('?ErrSomewhere...')
            return False


# 双向对比字典结构
class Comparative():
    _keylist = []
    _vallist = []
    __index = -1

    def __init__(self, dataA, dataB='', resourse='data'):
        self.add(dataA, dataB, resourse)

    def check(self, data):
        if data == '' or data is None:
            logger.error('数据不能为空！')
            return False
        if data in self._keylist or data in self._vallist:
            logger.error('禁止存在相同数据！')
            return False
        return True

    def _readfromdict(self, dictin):
        if isinstance(dictin, dict):
            for key in dictin.keys():
                value = dictin.get(key)
                if self.check(key) and self.check(value):
                    self._keylist.append(key)
                    self._vallist.append(value)
        else:
            logger.error('输入非dict类型')

    def get(self, data, default=None):
        if data in self._keylist:
            return self._vallist[self._keylist.index(data)]
        elif data in self._vallist:
            return self._keylist[self._vallist.index(data)]
        else:
            return default

    def add(self, dataA, dataB='', resource='data'):
        if resource == 'data':
            if self.check(dataA) and self.check(dataB):
                self._keylist.append(dataA)
                self._vallist.append(dataB)
                return True
            else:
                return False
        elif resource == 'dict':
            return self._readfromdict(dataA)


# 重构配置文件
class Config(Structure):
    typetree = Comparative(
        {int: b'\x01', str: b'\x02', bool: b'\x03', float: b'\x04', configTree: b'\x05', list: b'\x06'},
        resourse='dict')

    def __init__(self, data=None, cfgdata=None, Magic='cfg', file=None):
        super(Config, self).__init__(data, Magic, file)
        self._cfgread = False
        if cfgdata:
            self.cfg = configTree(importdata=cfgdata)
        else:
            self.cfg = configTree()
        self.version = RootData.get("Config_version")
        self.read = self.cfg
        self.__u = []

    def type(self, bytes):
        return self.typetree.get(bytes)

    def gettype(self, item):
        return self.typetree.get(type(item), default=b'\x02')

    def namelong(self, len):
        return '>' + 'c' * len

    def readfromType(self, type):
        if type == int:
            return struct.unpack('>i', self.readData(4))[0]
        if type == str:
            name_len = struct.unpack('>i', self.readData(4))[0]  # 命名长度
            return str(self.readData(name_len).decode())
        if type == bool:
            r = self.readData(1)
            if r == b'':
                return True
            else:
                return struct.unpack('>?', r)[0]
        if type == float:
            return struct.unpack('>f', self.readData(4))[0]
        if type == list:
            name_len = struct.unpack('>i', self.readData(4))[0]  # 命名长度
            return str(self.readData(name_len).decode())[1:-1:].split(',')
        # TODO:list有bug，不要用

    def encoder(self, mr):
        if type(mr) == int:
            return struct.pack('>i', mr)
        elif type(mr) == str:
            return struct.pack('>i', mr.encode().__len__()) + mr.encode()
        elif type(mr) == bool:
            return struct.pack('>?', mr)
        elif type(mr) == float:
            return struct.pack('>f', mr)
        elif type(mr) == list:
            return struct.pack('>i', str(mr).encode().__len__()) + str(mr).encode()
        else:
            return struct.pack('>i', str(mr).__len__()) + str(mr).encode()

    def set(self, name, value):
        return self.read.set(name, value)

    def get(self, name):
        return self.read.get(name)

    def listall(self):
        return self.read.listall()

    def remove(self, name):
        return self.read.remove(name)

    def seek(self, name):
        if name == '_root':
            self.read = self.cfg
            self.__u = []
            return True
        elif name == '..':
            u = self.__u
            if u.__len__() == 0:
                self.read = self.cfg
                logger.error("当前目录已达到_root！")
                return False
            else:
                self.read = self.cfg
                u.pop(-1)
                for i in u:
                    self.read = getattr(self.read, i)
                self.__u = u
                return True
        elif name in self.read.folder:
            self.__u.append(name)
            self.read = getattr(self.read, name)
            return True
        else:
            logger.error('当前分支下不存在名为"%s"的分支' % name)
            return False

    def delChild(self, name):
        return self.read.delChild(name)

    def addChild(self, name, data=None):
        return self.read.addChild(name, data)

    def _writeConfig(self, cfg, f, name, debug=False):
        f.write(struct.pack('>?', False))  # 非空预设
        if debug:
            logger.debug('<->%s:i%s f%s' % (cfg._root, cfg.item, cfg.folder))
        # TODO:如果folder和item都是空的 会出错
        for it in cfg.item:
            if cfg.get(it) != None:
                f.write(struct.pack('>h', it.__len__()))
                f.write(it.encode())
                f.write(self.gettype(cfg.get(it)))
                f.write(self.encoder(cfg.get(it)))
                f.write(struct.pack('>?', False))
                if debug:
                    logger.debug(
                        '<->[i]%s(%s): %s <%s>' % (it, it.__len__(), str(cfg.get(it)), str(type(cfg.get(it)))[8:-2:]))
        if cfg.folder == []:
            f.seek(f.tell() - 1)
            f.write(struct.pack('>?', True))  # 补充空集
            return [True, 'emp_folder', cfg._root]
        for fld in cfg.folder:
            f.write(struct.pack('>h', fld.__len__()))
            f.write(fld.encode())
            f.write(self.gettype(cfg.get(fld)))
            ret = self._writeConfig(getattr(cfg, fld), f, fld, debug)
            if debug:
                logger.debug('<->R%s' % ret)
        f.seek(f.tell() - 1)
        f.write(struct.pack('>?', True))  # 结束当前folder
        if cfg.item == []:
            if cfg.folder == []:
                return [True, 'emp_all', cfg._root]
            f.write(struct.pack('>?', True))  # item为空 补充结尾
            return [True, 'emp_item', cfg._root]
        f.write(struct.pack('>?', True))  # item和folder都非空 补充结尾
        return [True, 'full', cfg._root]

    def writeConfig(self, filename=None, debug=False):
        if hasattr(self, 'data'):
            if self._fileopen == True:
                self.data.close()
                self._fileopen = False
        if self._filename is not None:
            f = open(self._filename, 'wb+')
        elif not filename:
            logger.error("<!>未指定配置文件")
            return False
        else:
            f = open(filename, 'wb+')
        f.write(self.magic.encode())
        f.write(struct.pack('>f', self.version))
        f.write(struct.pack('>?', False))  # 非空预设
        if debug:
            logger.debug('<->--------WriteConfig-S------')
        for it in self.cfg.item:
            if self.cfg.get(it) != None:
                f.write(struct.pack('>h', it.__len__()))
                f.write(it.encode())
                f.write(self.gettype(self.cfg.get(it)))
                f.write(self.encoder(self.cfg.get(it)))
                f.write(struct.pack('>?', False))
        if self.cfg.folder == []:
            f.seek(f.tell() - 1)
            f.write(struct.pack('>?', True))  # 补充空集
            if debug:
                logger.debug('<->-----------WriteConfig-E-----------')
            return True
        for fld in self.cfg.folder:
            f.write(struct.pack('>h', fld.__len__()))
            f.write(fld.encode())
            f.write(self.gettype(self.cfg.get(fld)))
            ret = self._writeConfig(getattr(self.cfg, fld), f, fld, debug=debug)
            if debug:
                logger.debug('<->R%s' % ret)
        f.seek(f.tell() - 1)
        f.write(struct.pack('>?', True))  # 结束所有folder
        if debug:
            logger.debug('<->-----------WriteConfig-E-----------')
        return True

    def createConfig(self):
        self.version = RootData.get("Config_version")

    def readConfig(self, config=None, keepseek=False, inner=False, debug=False):
        # logger.system('<+>读取配置文件中...',flush=True)
        # TODO:处理空文件时异常：mrfzdata.mr ->list型数据
        # F = Config(cfgdata=json.load(open('.\MRFZdata\ArknightsGameData\excel\mission_table.json','rb')),Magic='mrfzd',file='mrfzdata2.mr')
        # D = Config(Magic='mrfzd',file='mrfzdata.mr')
        # R = Config(Magic='test',file='testcfg.t')
        # seek在mission->guide_1->unlockParam 166
        if config == None:
            config = self.cfg
        if self._fileopen:
            hand = self.data.tell()
        else:
            if hasattr(self, '_filename'):
                self.readFile(self._filename)
                hand = 0
            else:
                logger.error('<!>无可读取内容！配置不存在')
                return False
        if self._cfgread:
            self.cfg = configTree()
            config = self.cfg
        if self.checkHeader():
            self.version = struct.unpack('>f', self.readData(4))[0]
            if round(self.version, 1) < RootData.get("Config_version") and not inner:
                logger.error("<!>配置文件版本(%.1f)高于程序版本！无法读取" % self.version)
                return False
            elif round(self.version, 1) > RootData.get("Config_version") and not inner:
                logger.warning("<!>配置文件版本(%.1f)低于程序版本！保存时将使用当前版本存储配置！" % self.version)
            if keepseek:
                self.data.seek(hand)
            _ts = time.time()
            if not inner:
                if self.readfromType(bool):
                    logger.error("<!>配置是空的！")
                    return False
                if debug is True:
                    logger.debug('<+>-----------ReadConfig-S-----------')
            while True:
                try:
                    name_len = struct.unpack('>h', self.readData(2))[0]  # 命名长度
                    name = self.readData(name_len).decode()
                    type_ = self.type(self.readData(1))

                    if not type_ == configTree:  # list? ---->item
                        value = self.readfromType(type_)
                        config.set(name, value)
                        if debug is True:
                            logger.debug('<+>[%s]%s.%s(%s): %s' % (
                                self.data.tell(), config._root, name, name_len, str(type_)[8:-2:]))
                        if self.readfromType(bool):
                            if debug is True:
                                logger.debug('<+>[%s][t1]end,exit' % (self.data.tell()))
                            break
                    else:  # folder
                        config.addChild(name)
                        # ->
                        # empty folder ?
                        if self.readfromType(bool):
                            if debug is True:
                                logger.debug('<+>[%s][t2]end,exit' % (self.data.tell()))
                            break
                        # <-
                        self.readConfig(getattr(config, name), keepseek=True, inner=True, debug=debug)
                        if self.readfromType(bool):
                            if debug is True:
                                logger.debug('<+>[%s][t3]end,exit' % (self.data.tell()))
                            break
                        else:
                            self.data.seek(self.data.tell() - 1)
                except:
                    logger.error('<!>读取时出现错误 [seek:%s]' % self.data.tell())
                    # logger.system('<r>读取配置文件完成！[用时%f秒]' % _ts)
                    return False
            _ts = time.time() - _ts
            if not inner:
                self._cfgread = True
                if debug is True:
                    logger.debug('<+>[%s]-----------ReadConfig-E-----------' % self.data.tell())
                logger.system('<+>读取配置文件完成！[用时%.2f毫秒]' % (_ts * 1000))
            return True
        else:
            logger.error('<!>Magic Code不匹配！')
            return False

    def getConfigTree(self, prefix='', suffix='┣', root='r'):
        if root == 'r':
            root = self.read

        if prefix == '':
            m = '['
            for fldr in self.__u:
                m = m + '->' + fldr
            m = m + ']'
            print(m + root._root)
        for item in root.item:
            if root.item.index(item) == root.item.__len__() - 1:
                suffix = '┗ '
            else:
                suffix = '┣ '
            print(prefix + suffix + item + ":" + " <" + str(type(root.get(item)))[8:-2:] + ">" + str(root.get(item)))
        for folder in root.folder:
            if root.folder.index(folder) == root.folder.__len__() - 1:
                suffix = '┗ '
                prpr = prefix + '    '
            else:
                suffix = '┣ '
                prpr = prefix + '┃  '
            print(prefix + suffix + '' + folder + ":")
            self.getConfigTree(prpr, root=getattr(root, folder))
