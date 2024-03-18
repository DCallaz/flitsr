# FLITSR
A python implementation of the FLITSR fault localization tool for multiple
faults.
## Setup
### Requirements
* `python3`
* `numpy`
* `matplotlib` (optional, used for evaluation)
### Installation
To install FLITSR, simply clone this repository and run the `setup.sh` script.

Alternatively, if you do not want to run the `setup.sh` script, you can add the
following lines to your `.bashrc` manually:
```
export FLITSR_HOME="absolute/path/to/flitsr/directory"
export PATH="$FLITSR_HOME/bin:$PATH"
```

To test your installation, from any directory run:
```
flitsr
```
which should print the usage message.
## Basic usage
### Running FLITSR
To run the FLITSR algorithm and produce a suspiciousness ranking, simply use the
command:
```
flitsr <input>
```
where `<input>` is the directory containing the coverage files for GZoltar
input, or the file containing the coverage for TCM input. See the Input structure
section for more information on the types of input.

More advanced options and outputs are described in the Detailed usage section in
this README.
### Running evaluation
To run the full evaluation on FLITSR, simply use the command:
```
run_all [tcm]
```
in the top level directory for the dataset. If the `tcm` parameter is given, the
TCM format is assumed, otherwise GZoltar format is assumed.
### Input structure
FLITSR is a pure Spectrum-Based Fault Localization (SBFL) technique, and thus
only requires the collected coverage information from the execution of the test
suite over a system. FLITSR currently supports two input types:
1. TCM format, taken from ["More Debugging in Parallel"](https://www.fernuni-hagen.de/ps/prjs/PD/)
    ```
    #tests
    <test name> <status (PASSED | FAILED | ERROR)> [<exception>]
    .
    .
    .

    #uuts
    <element name> [| <bugId>]
    .
    .
    .

    #matrix
    <index above of element executed> <number of executions> ...
    .
    .
    .
    ```
    When using the `method` argument for FLITSR, `<element name>` must be of the format:
    `<java package name>.<class name>:<method name>:<line number>`.

    Note that this format is slightly different than that described on the [TCM
    webpage](https://www.fernuni-hagen.de/ps/prjs/PD/), for instance it does not
    require the exceptions for FAILED test cases and assumes a bug ID can be given
    for buggy elements. These differences are optional, as both this format
    __AND__ the format given on the TCM webpage are supported, as well as any
    combination of the two. In this way, the format accepted is a more relaxed
    format.
2. GZoltar format, which can be generated using the [GZoltar tool](https://gzoltar.com/).

    This splits the coverage information into three separate files:
    1. `tests.csv`:
        ```
        name,outcome,runtime,stacktrace
        <test name>,<status (PASS | FAIL)>[,<runtime>,<exception>]
        .
        .
        .
        ```
    2. `spectra.csv`:
        ```
        name
        <element name>[:<bugID>]
        .
        .
        .
        ```
        Where `<element name>` is of the format: `<java package name>$<class
        name>#<method name>:<line number>`. Note that because of this restriction,
        FLITSR only supports statement-level coverage in GZoltar format.
    3. `matrix.txt`:

        The test and element numbering in this file refers to the indexing of the
        tests and elements in the `tests.csv` and `spectra.csv` files respectively.
        ```
        <element 0 executed in test 1> <element 1 executed in test 1> ...
        <element 0 executed in test 2> <element 1 executed in test 2>
        .
        .
        .
        ```
## Detailed usage and script description
The use of the FLITSR tool and its associated scripts is described here in
detail.
### FLITSR script (`flitsr`)
Most of the main functionality of FLITSR and its related scripts can be accessed
by running the `flitsr` command. Running the command with no parameters will
give the help message containing all the valid arguements the script can take.
For ease of access, these are listed and described here:
```
Usage: flitsr <input file> [<metric>] [split] [method] [worst] [sbfl]
[first/avg/med/last] [one_top1/all_top1/perc_top1] [perc@n] [precision/recall]@x
[tiebrk/rndm/otie] [multi] [all] [only_fail] ['aba', 'mba_10_perc', 'mba_5_perc',
'mba_const_add', 'mba_dominator', 'mba_optimal', 'mba_zombie', 'oba']

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
* `multi`: Runs the FLITSR\* (i.e. multi-round) algorithm.
* `all`: Used in the evaluation of FLITSR against other techniques. Runs all
  metrics given in `suspicious.py` and both FLITSR and FLITSR\* extensions over
  each metric. Also enables all of the above evaluation calculations. Prints the
  results out to files named `[<flitsr method>_]<metric>.results` for each
  FLITSR method and metric.
* `aba/mba_<cutoff>/oba`: Cuts off the ranking using the given ABA, MBA or OBA
  cut-off point respectively. This affects both the rank output method and any
  calculations as given above.
### Running evaluation (`run_all`)
TODO
### Merging results (`merge`)
Results that are generated by `flitsr` and summarized by the `run_all` script can
be manually merged to produce averages using the `merge` script. This script
is called from within the `run_all` script, but only for individual results. To
do more complex merging, the `merge` script allows a number of useful arguments:
```
merge [rel] [recurse[=<x>]] [n=<a>,...] [tex]
```
* `rel`: Specifies that the input files denote relative figures and not
  absolute.
* `recurse[=<x>]`: Activates the scripts recursive mode. This makes the script
  recursively look in sub-directories of the current directory for results
  files. An optional maximum recurse limit `x` can be given.
* `[n=<a>,...]`: The presence of this arguments specifies that only particular
  `n`-fault versions should be considered, where the parameters `a` etc. denote
  these `n`'s. When used with the `recurse` argument, only `.results` files in
  sub-directories named `<n>-fault` will be considered.
* `tex`: Specifies that an additional output file should be generated that
  contains the results in a LaTeX table (in `.tex` format).
### Percentage at n plots (`percent_at_n`)
Once the merge script has been called, a `perc_at_n_results` file will be
generated from which you can plot the percentage at n graphs using the
`percent_at_n` script. To do so, use the command:
```
percent_at_n plot <perc_at_n_results> [mode] [metrics=[<metric>,...]]
      [flitsrs=[<metric>,...]] [linear/log] [all]
```
* `mode`: This argument causes the plots to be split by mode instead of metric.
* `metrics=[<metric>,...]`: An optional list of metrics to display
* `flitsrs=[<metric>,...]`: An optional list of metrics to display the FLITSR
  and FLITSR\* results for. Must be a subset of the `metrics` argument, if
  given.
* `linear/log`: Specifies whether the plot should display a linear or log
  x-scale. Default is log.
* `all`: This argument causes the plots to be condensed into one plot with all
  curves. This is incompatible with the `mode` argument.
### Results plots (`plot`)
NOTE: THIS SCRIPT IS CURRENTLY DEPRECATED
Once the merge script has been called, plots of the results can be generated
using the `plot` script. To use this script, use the command:
```
plot [sep] [rel] [tcm] [calcs=[<calc>,..]] [metrics=[<metric>,...]]
```
in the top-level directory of the project where results were collected. Where:
* `sep`: Specifies that each ????? will be plotted on a separate plot.
* `rel`: Plots the relative results (if available)
* `tcm`: Specifies that the project is in TCM format
* `calcs=[<calc>,...]`: An optional list of calculations to plot
* `metrics`: An optional list of metrics to display
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
