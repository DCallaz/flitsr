import sys
from flitsr.input import spectrumBuilder
from flitsr.calculations import percent_at_n

# load percent_at_n at package level
for module in (percent_at_n,):
    new_name = f'{__package__}.{module.__name__.rsplit(".")[-1]}'
    sys.modules[new_name] = sys.modules[module.__name__]

__all__ = [
    'flitsr',
    'merge',
    'percent_at_n',
    'plot'
]
