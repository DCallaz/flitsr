import sys
from typing import TextIO, Union, Any, Dict, List, Optional, Sequence
from numbers import Number
from flitsr.ranking import Rankings
from flitsr.calculations import BUModel, calcs, calcs_base
from flitsr.tie import Ties


def calculate(rankings: Rankings,
              calc_args: Dict[str, List[Optional[Dict[str, Any]]]],
              decimals: int = 2, file: Union[str, TextIO] = sys.stdout,
              bu_model: BUModel = BUModel.PERFECT, collapse: bool = False):
    if (isinstance(file, str)):
        file = open(file)
    ties: Ties = Ties(rankings, bu_model)
    for calc, lst_values in calc_args.items():
        calc_fn = calcs[calc]
        # iterate over each (unique) instance of the calculation
        seen = []
        for values in lst_values:
            if (values in seen):
                continue
            else:
                seen.append(values)
            parameters: Dict[str, Any] = {}
            if (values is not None):
                parameters.update(values)
            parameters['ties'] = ties
            parameters['collapse'] = collapse
            # get print name
            print_name = getattr(calcs_base[calc], '__print_name__')
            if (not isinstance(print_name, str)):
                print_name = print_name(**parameters)
            # get value & format (to decimal place)
            computed = calc_fn(**parameters)
            if (isinstance(computed, Number)):
                formatted = f'{computed:.{decimals}f}'
            elif (isinstance(computed, Sequence) and
                  all(isinstance(comp, Number) for comp in computed)):
                formatted = ','.join(f'{c:.{decimals}f}' for c in computed)
            else:
                formatted = str(computed)
            print(f'{print_name}: {formatted}', file=file)
