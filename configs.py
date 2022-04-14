import json
import os
from os.path import expandvars, expanduser, exists
from copy import deepcopy
from datetime import datetime


def raise_type_error(_needed, _supplied):
    TypeError(f"Invalid type, \"{_needed if type(_needed) is str else _needed.__name__}\" needed, "
              f"\"{type(_supplied).__name__}\" supplied")


class Configs:
    INTERNAL_PROPERTIES = {
        "__update_time__": int
    }

    class MissingDefaultConfigFilePathException(Exception):
        pass

    class NoConfigAvailableException(Exception):
        pass

    class ConfigFormatErrorException(Exception):
        pass

    class ReservedPropertyException(Exception):
        pass

    def recursive_check(self, _check):
        def _rec(_self, _input, _types):
            for _i, _v in _input.items():
                if _i in Configs.INTERNAL_PROPERTIES:
                    if type(_v) is not Configs.INTERNAL_PROPERTIES[_i]:
                        raise_type_error(type(_types[_i]), type(_v))
                    else:
                        continue
                if _i not in _types:
                    raise KeyError(f"Unrecognized property \"{_i}\" in config file")
                elif isinstance(_v, type(_types[_i])):
                    raise_type_error(type(_types[_i]), type(_v))
                elif isinstance(_v, dict):
                    if not isinstance(_types[_i], dict):
                        raise_type_error(type(_types[_i]), type(_v))
                elif isinstance(_v, list):
                    if len(_v) == 0:
                        continue
                    _uniq = set()
                    for _t in _types[_i]:
                        _uniq.add(type(_t))
                    if len(_uniq) != 1:
                        raise self.ConfigFormatErrorException(_uniq)
                    t = _types[_i][0]
                    if not all(map(lambda l: isinstance(l, type(t)), _v)):
                        raise_type_error(t, type(_v))

        _rec(self, _check, self.template)

    def __init__(self, template, data=None, config_path=None, write=False):
        self.template = deepcopy(template)
        self.data = None
        self.data = deepcopy(self.template)
        self.config_path = config_path
        if data is None and not write:
            if self.config_path is not None:
                self.read(self.config_path, update=True)
        elif not write:
            self.recursive_check(data)
            self.data.update(data)
        else:
            self.write()
        if "__update_time__" not in self.data:
            if config_path:
                mtime = os.stat(config_path).st_mtime
                self.set("__update_time__", mtime)

    @staticmethod
    def check_for_reserved(_key):
        if len(_key) >= 2 and _key[0:2] == "__" and _key not in Configs.INTERNAL_PROPERTIES:
            raise Configs.ReservedPropertyException

    def set(self, _key, _value):
        Configs.check_for_reserved(_key)

        if _key in self.template:
            if type(_value) is not type(self.template[_key]):
                raise_type_error(type(self.template[_key]), type(_value))
        elif _key in Configs.INTERNAL_PROPERTIES:
            if type(_value) is not type(Configs.INTERNAL_PROPERTIES[_key]):
                raise_type_error(type(Configs.INTERNAL_PROPERTIES[_key]), type(_value))
            else:
                self.set("__update_time__", datetime.now().timestamp())
        else:
            raise KeyError(_key)

        if type(_value) is dict:
            def _recursive_update(_input, _output):
                for _i, _v in _input.items():
                    if type(_v) is dict:
                        _recursive_update(_v, _output[_i])
                    else:
                        _output[_i] = _v

            _recursive_update(_value, self.data[_key])
        else:
            self.data[_key] = _value

    def get(self, key, path=False, expanduser_func=None):
        try:
            if path:
                if expanduser_func is None:
                    return expandvars(expanduser(self.data[key]))
                else:
                    return expandvars(expanduser_func(self.data[key]))
            else:
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
                elif self.config_path is not None:
                    _buffer = open(self.config_path, "w+")
                else:
                    raise self.MissingDefaultConfigFilePathException
            else:
                if type(_buffer) is str:
                    _buffer = open(_buffer, "w+")

            json.dump(self.data, _buffer, indent=4 if _indent else None)
        finally:
            if hasattr(_buffer, "close"):
                _buffer.close()

    def read(self, _buffer=None, update=True):
        if _buffer is None:
            if "config_file" in self.data:
                _buffer = open(self.data["config_file"])
            elif self.config_path is not None:
                _buffer = open(self.config_path)
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
