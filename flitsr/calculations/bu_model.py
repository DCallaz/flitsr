from enum import Enum, auto
from typing import Optional, Callable, Dict, Any, Set, Union, List
from argparse import ArgumentTypeError


class BUModelEnum(Enum):
    PERFECT = auto()
    IMPERFECT = auto()
    INEPT = auto()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


class BUModel:
    PERFECT: 'BUModel'
    INEPT: 'BUModel'
    IMPERFECT: 'BUModel'

    def __init__(self, model: Union['BUModel', BUModelEnum],
                 strategy: Optional[Callable[[int], int]] = None):
        if (isinstance(model, BUModelEnum)):
            self.model = model
        else:
            self.model = model.model
        self.strategy: Optional[Callable[[int], int]] = strategy

    def is_model(self, model: Union['BUModel', BUModelEnum]) -> bool:
        if (isinstance(model, BUModelEnum)):
            return self.model is model
        else:
            return self.model is model.model

    @classmethod
    def __class_getitem__(cls, model: str) -> 'BUModel':
        model_inst = getattr(cls, model)
        if (isinstance(model_inst, cls)):
            return model_inst
        else:
            raise AttributeError(f"type object '{cls.__name__}' has no model "
                                 f"'{model}'")

    def get_dict(self, faults: Dict[Any, Set[Any]]) \
            -> Dict[Any, int]:
        func: Callable[[int], int]
        if (self.model is BUModelEnum.PERFECT):  # perfect
            def func(x: int) -> int: return 1
        elif (self.model is BUModelEnum.INEPT):  # inept
            def func(x: int) -> int: return x
        elif (not self.strategy):            # default imperfect (mid-point)
            def func(x: int) -> int: return x//2
        else:                                # custom imperfect
            func = self.strategy
        bu_dict: Dict[Any, int] = {}
        for fault, fault_locs in faults.items():
            bu_dict[fault] = max(1, func(len(fault_locs)))
        return bu_dict

    def __repr__(self) -> str:
        src = ''
        if (self.strategy is not None and self.model is BUModelEnum.IMPERFECT):
            from inspect import getsource
            try:
                src = f' ({getsource(self.strategy).strip()})'
            except OSError:
                src = f' ({self.strategy})'
        return f'{self.model.name}' + f'{src}'

    @classmethod
    def get_types(cls) -> List['BUModel']:
        return [cls.PERFECT, cls.INEPT, cls.IMPERFECT]

    def __str__(self) -> str:
        return self.__repr__()

    @classmethod
    def from_string(cls, s: str) -> 'BUModel':
        try:
            return cls.__class_getitem__(s)
        except AttributeError:
            choices = ', '.join(f"'{d}'" for d in list(BUModelEnum))
            raise ArgumentTypeError(f"invalid choice: '{s}' "
                                    f"(choose from {choices})")


BUModel.PERFECT = BUModel(BUModelEnum.PERFECT)
BUModel.INEPT = BUModel(BUModelEnum.INEPT)
BUModel.IMPERFECT = BUModel(BUModelEnum.IMPERFECT)
