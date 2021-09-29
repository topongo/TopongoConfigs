import json
from os.path import expandvars, expanduser, exists
from copy import deepcopy


class Configs:
    class MissingDefaultConfigFilePathException(Exception):
        pass

    class NoConfigAvailableException(Exception):
        pass

    class ConfigFormatErrorException(Exception):
        pass

    def raise_type_error(self, _needed, _supplied):
        TypeError(f"Invalid type, \"{_needed if type(_needed) is str else _needed.__name__}\" needed, "
                  f"\"{type(_supplied).__name__}\" supplied")

    def recursive_check(self, _check):
        def _rec(_self, _input, _types):
            for _i, _v in _input.items():
                if _i not in _types:
                    raise KeyError(_i)
                elif type(_v) is not type(_types[_i]):
                    _self.raise_type_error(type(_types[_i]), type(_v))
                elif type(_v) is dict:
                    if type(_types[_i]) is not dict:
                        _self.raise_type_error(type(_types[_i]), type(_v))
                    _rec(_self, _v, _types[_i])
                elif type(_v) is list:
                    if len(_v) == 0:
                        continue
                    _uniq = set()
                    for _t in _types[_i]:
                        _uniq.add(type(_t))
                    if len(_uniq) != 1:
                        raise self.ConfigFormatErrorException(_uniq)
                    t = _types[_i][0]
                    if not all(map(lambda l: type(l) is t, _v)):
                        _self.raise_type_error(t, type(_v))

        _rec(self, _check, self.template)

    def __init__(self, template, data=None, config_path=None):
        self.template = deepcopy(template)
        self.data = None
        self.data = deepcopy(self.template)
        self._config_path = config_path
        if data is None:
            if self._config_path is not None:
                self.read(self._config_path, update=True)
        else:
            self.recursive_check(data)
            self.data.update(data)

    def set(self, _key, _value):
        if self.template[_key] == "path":
            if type(_value) is not str:
                self.raise_type_error("path (str)", type(_value))

        if type(_value) is type(self.template[_key]):
            self.data[_key] = _value
        elif type(_value) is dict:
            self.recursive_check({_key: _value})

            def _recursive_update(_input, _output):
                for _i, _v in _input.items():
                    if type(_v) is dict:
                        _recursive_update(_v, _output[_i])
                    else:
                        _output[_i] = _v

            _recursive_update(_value, self.data[_key])
        else:
            raise self.raise_type_error(self.template[_key], type(_value))

    def get(self, key):
        try:
            return self.data[key]
        except KeyError:
            raise KeyError(key)

    def keys(self):
        return self.data.keys()

    def write(self, _buffer=None, _indent=True):
        try:
            if _buffer is None:
                if "config_file" in self.data:
                    _buffer = open(expanduser(expandvars(self.data["config_file"])), "w+")
                elif self._config_path is not None:
                    _buffer = open(self._config_path, "w+")
                else:
                    raise self.MissingDefaultConfigFilePathException
            else:
                if type(_buffer) is str:
                    _buffer = open(_buffer, "w+")
            json.dump(self.data, _buffer, indent=4)
        finally:
            if hasattr(_buffer, "close"):
                _buffer.close()

    def read(self, _buffer=None, update=True):
        if _buffer is None:
            if "config_file" in self.data:
                _buffer = open(self.data["config_file"])
            elif self._config_path is not None:
                _buffer = open(self._config_path)
            else:
                raise self.MissingDefaultConfigFilePathException
        else:
            if type(_buffer) is str:
                _buffer = open(_buffer)
        try:
            _to_validate = json.load(_buffer)
        except json.decoder.JSONDecodeError:
            raise self.ConfigFormatErrorException
        self.recursive_check(_to_validate)
        if update:
            self.data.update(_to_validate)
        else:
            self.data = _to_validate
