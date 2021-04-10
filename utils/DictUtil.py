def ModifiableUpdate(self: dict, other: dict, iter_list=True):
    for k, v in other.items():
        if type(v) is dict:
            child = self.get(k, ModifiableDict())
            if child is None:
                child = ModifiableDict()
                dict.update(self, {k: child})
            dict.update(self, {k: ModifiableUpdate(child, v)})
        elif type(v) is list and iter_list:  # 只对list类起作用，对list的继承类由于不知道其构造无法初始化可能造成问题！
            for index, val in enumerate(v):
                if isinstance(val, dict):
                    v[index] = ModifiableDict(val)
            dict.update(self, {k: v})
        else:
            dict.update(self, {k: v})
    return self


def ModifiableDelete(self: dict, deleted: dict):
    for k, v in deleted.items():
        if isinstance(v, dict):
            if self.get(k) is not None:
                dict.update(self, {k: ModifiableDelete(self.get(k), deleted.get(k))})
        elif isinstance(v, list):
            for it in v:
                try:
                    self.get(k).pop(it)
                except (KeyError, AttributeError):
                    pass

    return self


def ModifiableSet(self: dict, keyPath: tuple, value):
    temp = self
    joinPath = []
    if not len(keyPath):
        raise KeyError(f"argument keyPath doesn't exist!")
    for path in keyPath[:-1]:
        joinPath.append(path)
        if not isinstance((temp := temp.get(path)), dict):
            raise KeyError(f"path {'.'.join(joinPath)} doesn't exist!")
    temp.update({keyPath[-1]: value})


class ModifiableDict(dict):
    def __init__(self, *args, **kwargs):
        super(ModifiableDict, self).__init__()
        self.update(dict(*args, **kwargs), iter_list=True)

    def update(self, __m, iter_list=False, **kwargs) -> None:
        ModifiableUpdate(self, __m, iter_list=iter_list)

    def getPaths(self, *path, default=None):
        if not path:
            raise ValueError('Path is empty!')
        _raw = self
        _dft = {}
        for _path in path[:-1]:
            _raw = _raw.get(_path, _dft)
        return _raw.get(path[-1], default)

    def set(self, *keyPathAndValue):
        if len(keyPathAndValue) < 2:
            raise ValueError('len(keyPathAndValue) must >= 2!')
        ModifiableSet(self, keyPathAndValue[:-1], keyPathAndValue[-1])

    def delete(self, other) -> None:
        ModifiableDelete(self, other)


def _check_type(base):
    if not isinstance(base, (type, type(None))):
        raise TypeError("base type need type or NoneType")
    return True


class PushableDict(dict):
    def __init__(self, kv: (dict, list) = None, base: type = None):
        _check_type(base)
        if kv is not None:
            super(PushableDict, self).__init__(kv) if base is None else super(PushableDict, self) \
                .__init__(zip(kv, [base() for _ in kv]))
        else:
            super(PushableDict, self).__init__()
        self.__base__ = base

    def set_base(self, base):
        _check_type(base)
        self.__base__ = base
        return self

    def has(self, key):
        return key in self.keys()

    def new(self, key):
        self.update({key: self.__base__()})

    def push(self, key, value, method=list.append, create: bool = False):
        if key in self.keys():
            try:
                method(self.get(key), value)
                return True
            except Exception as e:
                return False
        elif create:
            if self.__base__ is None:
                return False
            self.update({key: self.__base__()})
            return self.push(key, value, method, create)
        return self

    def pushs(self, key, *values, method=list.append, create=False):
        for val in values:
            self.push(key, val, method, create)
        return self

    def where(self, value):
        for _ in self:
            if value in self.get(_):
                return _

    def wheres(self, values):
        ret = []
        for value in values:
            ret.append(self.where(value))
        return ret


class ItemDict(dict):
    def __init__(self, *args, **kwargs):
        super(ItemDict, self).__init__(*args, **kwargs)
        self._I = dict()
        for k, v in self['items'].items():
            self._I.setdefault(v['name'], k)

    def getByCNName(self, cnName: str):
        return self._I.get(cnName)
