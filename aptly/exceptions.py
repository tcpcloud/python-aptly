# -*- coding: utf-8 -*-


class AptlyException(Exception):
    def __init__(self, res, msg):
        Exception.__init__(self, msg)
        self.res = res


class NoSuchPublish(Exception):
    pass
