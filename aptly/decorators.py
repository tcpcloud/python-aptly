# -*- coding: utf-8 -*-


class CachedMethod(object):
    """
    Decorator for caching of function results
    """
    def __init__(self, function):
        self.function = function
        self.mem = {}

    def __call__(self, *args, **kwargs):
        cached = kwargs.pop('cached', True)
        if cached is True:
            if (args, str(kwargs)) in self.mem:
                return self.mem[args, str(kwargs)]

        tmp = self.function(*args, **kwargs)
        self.mem[args, str(kwargs)] = tmp
        return tmp

    def __get__(self, obj, objtype):
        """ Support instance methods """
        import functools
        return functools.partial(self.__call__, obj)
