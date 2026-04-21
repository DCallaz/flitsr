from enum import Enum, auto
from typing import Optional, Callable, Dict, Any, Set, Union
from argparse import ArgumentTypeError


class BUModelEnum(Enum):
    PERFECT = auto()
    DEFECTIVE = auto()
    INEPT = auto()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()


class BUModel:
    PERFECT: 'BUModel'
    INEPT: 'BUModel'
    DEFECTIVE: 'BUModel'

    def __init__(self, model: Union['BUModel', BUModelEnum],
                 strategy: Optional[Callable[[int], int]] = None):
        if (isinstance(model, BUModelEnum)):
            self.model = model
        else:
            self.model = model.model
        self.strategy: Optional[Callable[[int], int]] = strategy

    def is_model(self, model: Union['BUModel', BUModelEnum]):
        if (isinstance(model, BUModelEnum)):
            return self.model is model
        else:
            return self.model is model.model

    @classmethod
    def __class_getitem__(cls, model):
        return getattr(cls, model)

    def get_dict(self, faults: Dict[Any, Set[Any]]) \
            -> Dict[Any, int]:
        if (self.model is BUModelEnum.PERFECT):  # perfect
            def func(x): return 1
        elif (self.model is BUModelEnum.INEPT):  # inept
            def func(x): return x
        elif (not self.strategy):            # default defective (mid-point)
            def func(x): return x//2
        else:                                # custom defective
            func = self.strategy
        bu_dict: Dict[Any, int] = {}
        for fault, fault_locs in faults.items():
            bu_dict[fault] = max(1, func(len(fault_locs)))
        return bu_dict

    def __repr__(self) -> str:
        src = ''
        if (self.strategy is not None and self.model is BUModelEnum.DEFECTIVE):
            from inspect import getsource
            try:
                src = f' ({getsource(self.strategy).strip()})'
            except OSError:
                src = f' ({self.strategy})'
        return f'{self.model.name}' + f'{src}'

    @classmethod
    def get_types(cls):
        return [cls.PERFECT, cls.INEPT, cls.DEFECTIVE]

    def __str__(self) -> str:
        return self.__repr__()

    @classmethod
    def from_string(cls, s):
        try:
            return getattr(cls, s)
        except KeyError:
            choices = ', '.join(f"'{d}'" for d in list(BUModelEnum))
            raise ArgumentTypeError(f"invalid choice: '{s}' "
                                    f"(choose from {choices})")


BUModel.PERFECT = BUModel(BUModelEnum.PERFECT)
BUModel.INEPT = BUModel(BUModelEnum.INEPT)
BUModel.DEFECTIVE = BUModel(BUModelEnum.DEFECTIVE)
