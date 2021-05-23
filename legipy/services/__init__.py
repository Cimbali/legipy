# coding: utf-8

import requests

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = (super(Singleton, cls)
                                   .__call__(*args, **kwargs))
        return cls._instances[cls]


class Service(object):
    backend = requests
    def get(self, *args, **kwargs):
        return self.backend.get(*args, **kwargs)
