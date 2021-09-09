import json


class Configs:
    def __raise_type_error(self, __needed, __supplied):
        TypeError(f"Invalid type, \"{__needed if type(__needed) is str else __needed.__name__}\" needed, "
                  f"\"{type(__supplied).__name__}\" supplied")

    def __recursive_check(self, __check):
        def __rec(__self, __input, __types):
            for __i, __v in __input.items():
                if __i not in __types:
                    raise KeyError(__i)
                elif type(__v) is not __types[__i]:
                    __self.__raise_type_error(__types[__i], type(__v))
                elif __types[__i] == "path" and type(__v) is not str:
                    __self.__raise_type_error("path (str)", type(__v))
                elif type(__v) is dict:
                    if type(__types[__i]) is not dict:
                        __self.__raise_type_error(type(__types[__i]), type(__v))
                    __self.__recursive_check(__self, __v, __types[__i])
                elif type(__v) is list:
                    t = __types[__i][0]
                    if not all(map(lambda l: type(l) is t, __v)):
                        __self.__raise_type_error(t, type(__v))

        __rec(self, __check, self.types)

    def __init__(self, types, data):
        self.types = types
        self.__recursive_check(data)
        self.data = data

    def set(self, __key, __value):
        if self.types[__key] == "path":
            if type(__value) is not str:
                self.__raise_type_error("path (str)", type(__value))

        if type(__value) is self.types[__key]:
            self.data[__key] = __value
        elif type(__value) is dict:
            self.__recursive_check({__key: __value})

            def __recursive_update(__input, __output):
                for __i, __v in __input.items():
                    if type(__v) is dict:
                        __recursive_update(__v, __output[__i])
                    else:
                        __output[__i] = __v

            __recursive_update(__value, self.data[__key])
        else:
            raise self.__raise_type_error(self.types[__key], type(__value))

    def get(self, key):
        try:
            return self.data[key]
        except KeyError:
            raise KeyError(key)

    def keys(self):
        return self.data.keys()

    def write(self, __buffer=None):
        try:
            if __buffer is None:
                __buffer = open(self.data["config_file"], "w+")
            json.dump(self.data, __buffer)
        finally:
            __buffer.close()

    def read(self, __buffer=None):
        try:
            if __buffer is None:
                __buffer = open(self.data["config_file"])
            self.data = json.load(__buffer)
        finally:
            __buffer.close()