class Borg:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class GlobalDict(Borg):
    d = {}

    def __init__(self):
        Borg.__init__(self)

    @staticmethod
    def store(key, value):
        obj = GlobalDict()
        obj.d[key] = value

    def get(self, key):
        obj = GlobalDict()
        return obj.d[key]
