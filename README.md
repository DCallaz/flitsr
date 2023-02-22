# FLITSR
A python implementation of the FLITSR fault localization tool for multiple
faults.
## Usage
The use of the FLITSR tool and its associated scripts is described here in
detail.
### FLITSR script (`flitsr`)
Most of the main functionality of FLITSR and its related scripts can be accessed
by running the `flitsr` command. Running the command with no parameters will
give the help message containing all the valid arguements the script can take.
For ease of access, these are listed and described here:
```
Usage: flitsr <input file> [<metric>] [split] [method] [worst] [sbfl] [tcm]
[first/avg/med/last] [one_top1/all_top1/perc_top1] [perc@n] [precision/recall]@x
[tiebrk/rndm/otie] [multi/multi2] [all] [only_fail] ['aba', 'mba_10_perc',
'mba_5_perc', 'mba_const_add', 'mba_dominator', 'mba_optimal', 'mba_zombie',
'oba']

Where <metric> is one of: ['barinel', 'dstar', 'gp13', 'harmonic', 'hyperbolic',
'jaccard', 'naish2', 'ochiai', 'overlap', 'tarantula', 'zoltar']
```
* `<input file>`: The coverage file (TCM) or directory (GZoltar) containing the
  coverage collected for the system over the test suite
* `<metric>`: The underlying (SBFL) metric to use when either ranking (if the
  `sbfl` option is given), or running the FLITSR algorithm
* `split`: When given, this option causes faults that are a combination of two
  or more sub-faults in mutually exclusive parts of the system to be split into
  separate identified faults. As a by-product this also drops faults that are
  not exposed by failing tests.
* `method`: The default for FLITSR is to use the collected coverage as-is and
  merely produce the ranking in terms of the names/labels given to the elements.
  Alternatively, using this option, FLITSR can assume the coverage given is a
  statement level coverage, and will attempt to collapse this coverage to
  produce a method level coverage result. This collapse is done by constructing
  a coverage matrix with only the method names, where the execution of a method
  is determined by the union of the executions of its statements. Bugs added to
  the coverage are handled in a similar fashion.
* `worst`: When using a multi-fault fixing cut-off strategy to produce
  rankings, FLITSR by default assumes the best case performance. This can be
  toggled by giving this option to give the worst case performance instead.
* `sbfl`: Disables the FLITSR algorithm so that only the base metric is used
  to produce the ranking. This is equivalent to using the base metric as-is, but
  allows the user to run these metrics within the FLITSR framework.
* `tcm`: Specifies that the input is of the TCM format type, which is a single
  file containing the coverage information and bug locations. More information
  on the TCM format can be found at the [TCM homepage](https://www.fernuni-hagen.de/ps/prjs/PD/)
* The following arguments replace the default ranking output of FLITSR with
  evaluation calculations. Multiple of the following arguments can be given in
  the same call:
  * `first/avg/med/last`: Produces wasted effort calculations. The wasted effort
    calculations that can be generated are to the first, median, average, and
    last faults respectively.
  * `one_top1/all_top1/perc_top1`: Produces TOP1 calculations. The TOP1
    calculations that can be produced are:
      * `one_top1`: A boolean value indicating whether at least one fault was
        found in the top1 group
      * `all_top1`: The number of faults found in the top1 group
      * `percent_top_1`: The percentage of faults found in the top1 group.
  * `perc@n`: Produces the percentage-at-N values. The output of this
    calculation is a list of ranks of all found faults, preceeded by the number
    of elements in the system. This can be used to generate percentage-at-N/recall
    graphs.
  * `precision/recall@<x>`: Produces precision/recall values at a given rank
    `<x>`. Both precision and recall calculations determine the amount of faults
    `f` found within a certain cutoff point `x` after which precision calculates
    `f/x` and recall `f/n` where `n` is the total number of faults in the system.
* `tiebrk/rndm/otie`: Specifies the tiebreaking strategy to use for FLITSR and
  the localization. `tiebrk` breaks ties using only execution counts, `rndm` by
  randomly ordering, and `otie` by using the original base metric ranking (in the
  case of FLITSR) and by execution counts otherwise.
* `multi/multi2`: Runs the FLITSR\* (i.e. multi-round) algorithm.
TODO: complete
### Bug distribution (`distro`)
In the evaluation of FLITSR over multi-fault datasets it is sometimes useful to
know the distribution of faults in the datasets. For this purpose, the `distro`
script is available to compute the distribution of faults in the _TCM_ dataset.
It can be used by navigating to the base directory for any _TCM_ project and
using the command
```
distro
```
This will produce a distro.txt file containing the data bins for the fault
distributions, which can then be plotted as a bar chart by using the `distro.py`
script as follows:
```
python3 $FLITSR_HOME/distro.py distro.txt
```
