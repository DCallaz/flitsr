import sys
from typing import TextIO, Union, Any, Dict, List, Optional, Iterable
from numbers import Number
from flitsr.ranking import Rankings
from flitsr.calculations import BUModel, calcs
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
            computed = calc_fn(**parameters)
            print_name = getattr(calc_fn, '__print_name__')
            if (not isinstance(print_name, str)):
                print_name = print_name(**parameters)
            if (isinstance(computed, Number)):
                print(f'{print_name}: {computed:.{decimals}f}', file=file)
            elif (isinstance(computed, Iterable) and
                  all(isinstance(comp, Number) for comp in computed)):
                all_form: List[str] = []
                for comp in computed:
                    all_form.append(f'{comp:.{decimals}f}')
                computed = ','.join(all_form)
                print(f'{print_name}: {computed}', file=file)
            else:
                print(f'{print_name}: {computed}', file=file)
