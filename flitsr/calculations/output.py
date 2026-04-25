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
    ties: Ties = Ties(rankings, bu_model)
    for calc, lst_values in calc_args.items():
        calc_fn = calcs[calc]
        # iterate over each (unique) instance of the calculation
        for values in set(lst_values):
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
                print(f'{print_name}: {computed:.{decimals}f}')
            elif (isinstance(computed, Iterable) and
                  all(isinstance(comp, Number) for comp in computed)):
                all_form: List[str] = []
                for comp in computed:
                    all_form.append(f'{comp:.{decimals}f}')
                computed = ','.join(all_form)
                print(f'{print_name}: {computed}')
            else:
                print(f'{print_name}: {computed}')

    # if (args.weff):
    #     if ("first" in weff):
    #         print("wasted effort (first): {:.{}f}".format(
    #             weffort.first(ties, collapse),
    #             decimals), file=file)
    #     if ("avg" in weff):
    #         print("wasted effort (avg): {:.{}f}".format(
    #             weffort.average(ties, collapse),
    #             decimals), file=file)
    #     if ("med" in weff):
    #         print("wasted effort (median): {:.{}f}".format(
    #             weffort.median(ties, collapse),
    #             decimals), file=file)
    #     if ("last" in weff):
    #         print("wasted effort (last): {:.{}f}".format(
    #             weffort.last(ties, collapse),
    #             decimals), file=file)
    #     for nth in [w for w in weff if isinstance(w, int)]:
    #         print("wasted effort ({}): {:.{}f}".format(
    #             nth, weffort.nth(ties, int(nth), collapse),
    #             decimals), file=file)
    # if (top1):
    #     for entry in top1:
    #         if (entry[0] == 'all'):
    #             atp = top.all_top_n(ties, entry[1], collapse=collapse)
    #             print(f"all top {entry[1]}: {atp:.{decimals}f}", file=file)
    #         elif (entry[0] == 'one'):
    #             otp = top.one_top_n(ties, entry[1], collapse=collapse)
    #             print(f"one top {entry[1]}: {otp:.{decimals}f}", file=file)
    #         elif (entry[0] == 'perc'):
    #             ptp = top.perc_top_n(ties, entry[1], collapse=collapse)
    #             print(f"perc top {entry[1]}: {ptp:.{decimals}f}",
    #                   file=file)
    # if (perc_at_n):
    #     bumps = percent_at_n.getBumps(ties, collapse=collapse)
    #     if ('perc' in perc_at_n):
    #         form = ','.join(['{{:.{}f}}'.format(decimals)]*len(bumps))
    #         print("percentage at n:", form.format(*bumps), file=file)
    #     if (any([a in perc_at_n for a in ['auc', 'pauc', 'lauc']])):
    #         auc = percent_at_n.auc_calc(
    #                 percent_at_n.combine([(bumps[0], bumps[1:])]))
    #         if ('auc' in perc_at_n):
    #             print("auc:", auc, file=file)
    #         if ('pauc' in perc_at_n):
    #             optimal = percent_at_n.auc_calc([(0.0, 100.0)])
    #             print("pauc:", "{:.{}f}".format(auc/optimal, decimals),
    #                   file=file)
    #         if ('lauc' in perc_at_n):
    #             optimal = percent_at_n.auc_calc([(0.0, 100.0)])+1
    #             lauc = abs(1-log(optimal-auc, optimal))
    #             print("lauc:", "{:.{}f}".format(lauc, decimals), file=file)
    # if (prec_rec):
    #     for entry in prec_rec:
    #         if (entry[0] == 'p'):
    #             p = precision_recall.precision(entry[1], ties,
    #                                            collapse=collapse)
    #             print("precision at {}: {:.{}f}".format(entry[1], p,
    #                                                     decimals), file=file)
    #         elif (entry[0] == 'r'):
    #             r = precision_recall.recall(entry[1], ties,
    #                                         collapse=collapse)
    #             print("recall at {}: {:.{}f}".format(entry[1], r,
    #                                                  decimals), file=file)
    # if (faults):
    #     if ("num" in faults):
    #         print("fault number: {}".format(len(ties.faults)), file=file)
    #     if ("ids" in faults):
    #         print("fault ids: {}".format(list(ties.faults.keys())),
    #               file=file)
    #     if ("elems" in faults):
    #         print("fault elements: {}".format([e for es in ties.faults.values()
    #                                            for e in es]), file=file)
    #     if ("all" in faults):
    #         print("fault info: {}".format(ties.faults), file=file)
