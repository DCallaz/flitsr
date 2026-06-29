def test(i: int, s: str):
    pass


class P:
    def __init__(self, param_we_dont_have):
        pass

    def test2(self, i: int, s: str = 's'):
        pass

    @staticmethod
    def test3(i: int, s: str):
        pass

    @classmethod
    def test4(cls, i: int, s: str):
        pass


setattr(test, '__choices__', dict())
getattr(test, '__choices__')['s'] = ['a', 'b']

setattr(P.test3, '__choices__', dict())
getattr(P.test3, '__choices__')['s'] = ['a', 'b']
