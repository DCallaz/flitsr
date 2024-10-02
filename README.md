# FLITSR
A python implementation of the FLITSR fault localization tool for multiple
faults.
## Setup
### Requirements
* `python3`
### Installation
To install FLITSR, simply clone this repository and run the `setup.sh` script.

**Alternatively**, if you do not want to run the `setup.sh` script, you run the
following lines, or add them to your `.bashrc` file for future sessions:
```
export FLITSR_HOME="absolute/path/to/flitsr/directory"
export PATH="$FLITSR_HOME/bin:$PATH"
```

Then run the following commands to set up FLITSR:

```
python -m venv "$FLITSR_HOME/.venv"
$FLITSR_HOME/.venv/bin/pip install -r "$FLITSR_HOME/requirements.txt"
```

To test your installation, from any directory run:
```
flitsr -h
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
run_all [-t [<extension>]/-g]
```
in the top level directory for the dataset. If the `-t` option is given (with an
optional file extension), then the TCM format is assumed, otherwise if the `-g`
option is given, Gzoltar format is assumed.

See *[the section on the run_all script](#running-evaluation-run_all)* for more
details.
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
by running the `flitsr` command. Running the command with the `-h` or `--help`
options will give the help message containing all the valid arguments the script
can take. For ease of access, these are listed and described here:
```
usage: flitsr [-h] [-o OUTPUT] [--csv] [-m METRIC] [-s] [--multi]
              [-i {flitsr,reverse,original}] [-r] [-c] [--split] [--collapse]
              [-a] [--no-override] [-d DECIMALS] [--tiebrk] [--rndm] [--otie]
              [--first] [--avg] [--med] [--last] [--weffort N] [--one-top1]
              [--all-top1] [--perc-top1] [--perc@n] [--auc] [--pauc] [--lauc]
              [--precision-at x] [--recall-at x] [--fault-num] [--fault-ids]
              [--fault-elems] [--fault-all] [-p ALGORITHM] [--artemis]
              [--cutoff-eval MODE] [--cutoff-strategy STRATEGY]
              input
```
#### Positional arguments:
* `input`: The coverage file (TCM) or directory (GZoltar) containing the
  coverage collected for the system over the test suite
#### Options:
* `-h`, `--help`: show this help message and exit
* `-o OUTPUT`, `--output OUTPUT`: Specify the output file to use for all output
  (default: STDOUT).
* `--csv`: By default FLITSR will output the ranking in it's own FLITSR ranking
  format. Enabling this option will allow FLITSR to output the ranking in CSV
  format compatible with GZoltar's CSV ranking format instead.
* `-m METRIC`, `--metric METRIC`: The underlying (SBFL) metric to use when
  either ranking (if the sbfl option is given), or running the FLITSR algorithm.
  Option may be supplied multiple times to run multiple metrics. Specifying
  multiple metrics will output the results of each metric to a seperate file
  using the metric's name instead of stdout. Allowed values are: \[ample,
  anderberg, arith_mean, barinel, cohen, dice, dstar, euclid, fleiss, geometric,
  goodman, gp13, hamann, hamming, harmonic, hyperbolic, jaccard, kulczynski1,
  kulczynski2, m1, m2, naish2, ochiai, ochiai2, overlap, rogers_tanimoto,
  rogot1, rogot2, russell_rao, scott, simpl_match, sokal, sorensen_dice,
  tarantula, wong1, wong2, wong3, zoltar] (default: ochiai)
* `-s`, `--sbfl`: Disables the FLITSR algorithm so that only the base metric is
  used to produce the ranking. This is equivalent to using the base metric
  as-is, but allows the user to run these metrics within the FLITSR
  framework
* `--multi`: Runs the FLITSR\* (i.e. multi-round) algorithm
* `-i METHOD`, `--internal-ranking METHOD`: Specify the order in which the
  elements of each FLITSR basis are ranked. "flitsr" uses the order that FLITSR
  returns the basis in (i.e. from FLITSRs lowest to highest recursion depth),
  which aligns with FLITSRs confidence for each element being a fault. "reverse"
  uses the reverse of "flitsr" (i.e. the order in which FLITSR identifies the
  elements) which gives elements that use a larger part of the original test
  suite first. "original" returns the elements based on their original positions
  in the ranking produced by the base SBFL metric used by FLITSR.
* `-r`, `--ranking`: Changes flitsr's expected input to be an SBFL ranking
  in Gzoltar or FLITSR format (determined automatically), instead of the usual
  coverage, and produces the specified calculations (or just the ranking if no
  calculations are given). NOTE: any non-output based options will be ignored
  with this option
* `-c`, `--method`: The default for FLITSR is to use the collected
  coverage as-is and merely produce the ranking in terms of the names/labels
  given to the elements. Alternatively, using this option, FLITSR can assume the
  coverage given is a statement level coverage, and will attempt to collapse
  this coverage to produce a method level coverage result. This collapse is done
  by constructing a coverage matrix with only the method names, where the
  execution of a method is determined by the union of the executions of its
  statements. Bugs added to the coverage are handled in a similar
  fashion.
* `-split`: When given, this option causes faults that are a combination of two
  or more sub-faults in mutually exclusive parts of the system to be split into
  separate identified faults. As a by-product this also drops faults that are
  not exposed by failing tests
* `-collapse`: Collapse dynamic basic-block groups into singular elements for
  the ranking an calculations
* `-a`, `--all`: Used in the evaluation of FLITSR against other techniques.
  Runs all metrics given in suspicious.py and both FLITSR and FLITSR\* extensions
  over each metric. Also enables all of the above evaluation calculations. Prints
  the results out to files named `[<flitsr method>_]<metric>.run` for each
  FLITSR method and metric
* `--no-override`: By default FLITSR will override the output file(s) if they
  already exist, printing a warning message. This option instead allows FLITSR
  to leave output files that already exist, skipping that output and continuing
  with the rest of the outputs (if any)
* `-d DECIMALS`, `--decimals DECIMALS`: Sets the precision (number of decimal
  points) for the output of all of the calculations (default: 2)
* `-p ALGORITHM`, `--parallel ALGORITHM`: Run one of the parallel debugging
  algorithms on the spectrum to produce multiple spectrums, and process all
  other options on each spectrum. Allowed values are: [bdm, msp, hwk, vwk]
* `--artemis`: Run the ARTEMIS technique on the spectrum to produce the ranked
  lists. This option my be combined with FLITSR and parallel to produce a hybrid
  technique.
* `--cutoff-eval MODE`: Specifies the performance mode to use when using a
  multi-fault fixing cut-off strategy to produce rankings. Allowed values are:
  \[worst, best, resolve] (default worst)
* `--cutoff-strategy STRATEGY`: Cuts off the ranking using the given
  strategy's cut-off point. This affects both the rank output method and any
  calculations. Allowed values are: \[aba, basis, mba_10_perc, mba_5_perc,
  mba_const_add, mba_dominator, mba_optimal, mba_zombie, oba] (default None).
  For basis, an optional value n may be given (e.g. basis=n) that determines the
  number of bases included before the cutoff

#### Tie breaking strategy:
  Specifies the tie breaking strategy to use for FLITSR and the localization

* `-tiebrk`: Breaks ties using only execution counts
* `-rndm`: Breaks ties by a randomly ordering
* `-otie`: Breaks ties by using the original base metric ranking (in the case
  of FLITSR) and by execution counts otherwise

#### Calculations:
  The following arguments replace the default ranking output of FLITSR with
  evaluation calculations. Multiple of the following arguments can be given
  in the same call.

##### Wasted effort:
* `-first`: Display the wasted effort to the first fault
* `-avg,` `--average`: Display the wasted effort to the average fault
* `--med`, `--median`: Display the wasted effort to the median fault
* `-last`: Display the wasted effort to the last fault
* `--weffort N`: Display the wasted effort to the Nth fault
##### Top1:
* `-one-top1`: Display a boolean value indicating whether at least one fault
  was found in the TOP1 group (elements with the highest suspiciousness
* `-all-top1`: Display the number of faults found in the top1 group
* `-perc-top1`: Display the percentage of faults found in the top1 group
##### Percentage at n:
* `--perc@n`, `--percent-at-n`: Produces the percentage-at-N values (i.e. the
  percentage of faults found at N% of code inspected). The output of the perc@n
  calculation is a list of ranks of all found faults, preceded by the number of
  elements in the system, which can be used to generate
  percentage-at-N/recall graphs
* `--auc`, `--area-under-curve`: Dislpays the area under the curve produced by
  the percentage-at-N calculation
* `--pauc`, `--percent-area-under-curve`: Dislpays the area under the curve
  produced by the percentage-at-N calculation as a percentage of the maximum
  possible value (i.e. closest to perfect recall)
* `--lauc`, `--log-area-under-curve`: Dislpays the area under the curve
  produced by the percentage-at-N calculation as a logarithmic percentage of the
  maximum possible value (i.e. closest to perfect recall). The logarithmic
  effect causes lower ranks to have a greater effect on the value, which
  corresponds to the lower ranks being more useful to the developer
##### Precision and recall:
* `--precision-at x`: Displays precision values at a given rank `x`. Precision
  is the amount of faults f found within the cut-off point `x`, out of the
  number of elements seen (i.e. f/x). Can be specified multiple times
* `--recall-at x`: Displays recall values at a given rank `x`. Recall is
  the amount of faults f found within the cut-off point `x`, out of the total
  number of faults n (i.e. f/n). Can be specified multiple times
##### Faults:
* `--fault-num`: Display the number of faults in the program
* `--fault-ids`: Display the IDs of the faults in the program
* `--fault-elems`: Display the elements that are faulty in the program
* `--fault-all`: Display all info of the faults in the program

### Running evaluation (`run_all`)
The flitsr framework comes with the `run_all` script which enables large
experiments to be run easily. The script can be run in any top-level directory
with coverage files below. In order to properly find the files, the script can
be run with a specified depth, and/or the type of coverage (TCM or Gzoltar).
Since TCM files can have any extension, you may also optionally provide the
extension to use for your TCM files; If left unset, the default extension is "\*"
(i.e. anything).

The `run_all` script has the following options (which can be accessed by running
the script with the `-h` flag):
```
USAGE: run_all [-h] [-b <base dir>] [-m metric[,metric...]] [-d <depth>/-t [<ext>]/-g] [-c <cores>] [-r] [-a <flitsr arg>]
  where:
    -h                    : Prints this USAGE message
    -m metric[,metric...] : Runs only the given metrics (can be specified multiple times)
    -b <base dir>         : Set the base directory for running in to <base dir>
    -d <depth>            : Specifies the depth at which to look for inputs
    -t [<extension>]      : Look only for TCM type inputs (with optional extension <extension>)
    -g                    : Look only for GZoltar type inputs
    -c <cores>            : Sets the number of cores to run in parallel on (default automatic)
    -r                    : Recover from a partial run_all run by re-using existing files
    -a <flitsr arg>       : Specify an argument to give to the flitsr program
```
### Merging results (`merge`)
Results that are generated by `flitsr` and summarized by the `run_all` script can
be manually merged to produce averages using the `merge` script. This script
is called from within the `run_all` script, but only for individual results. To
do more complex merging, the `merge` script allows a number of useful arguments:
```
usage: merge [-h] [-R] [-r [X]] [-t [FILE]] [-p [FILE]] [-i] [-o FILE]
             [-d DECIMALS] [-g {metric,type}] [-c CALC [CALC ...]]
             [--percentage CALC [CALC ...]] [-f [METRIC [METRIC ...]]]
             [-m METRIC [METRIC ...]] [-n NS [NS ...]]
```
* `-h`, `--help`: show this help message and exit
* `-R`, `--relative`: Compute relative values instead of absolute values
* `-r [X]`, `--recurse [X]`: Activates the scripts recursive mode. This makes
    the script recursively look in sub-directories of the current directory for
    results files. An optional maximum recurse limit X can be given.
* `-t [FILE]`, `--tex [FILE]`: Specifies that an additional output file should
    be generated that contains the results in a LaTeX table (in .tex format). By
    default this is stored in results.tex, but an optional filename FILE may be
    given
* `-p [FILE]`, `--perc@n [FILE]`: Specifies that an additional output file should
    be generated that contains the percentage-at-n results. By default this is
    stored in `perc_at_n_results`, but an optional filename FILE may be given
* `-i`, `--inline-perc@n`:   Instead of producing a separate percentage-at-n
    file, place the results inline in the results file
* `-o FILE`, `--output FILE`: Store the results in the file with filename FILE.
    By default the name `results` is used
* `-d DECIMALS`, `--decimals DECIMALS`: Sets the precision (number of decimal
    points) for the output of all of the calculations Does not impact
    percentage-at-n values. (default 24, i.e. all python- stored significance).
* `-g {metric,type}`, `--grouping-order {metric,type}`: Specifies the way in which
    the output should be grouped. "metric" groups first by metrics and then by
    types, "type" does the opposite (default metric)
* `-c CALC [CALC ...]`, `--calcs CALC [CALC ...]`: Specify the list of
    calculations to include when merging. By default all available calculations
    are included. NOTE: the names of the calculations need to be found in the
    corresponding `.results` files
* `--percentage CALC [CALC ...]`: Specify calculations that must be intepreted as
    a percentage value. NOTE: the names of the calculations need to be found in
    the corresponding .results files
* `-f [METRIC [METRIC ...]]`, `--flitsrs [METRIC [METRIC ...]]`: Specify the
    metrics for which to display FLITSR and FLITSR* values for. By default all
    metric's FLITSR and FLITSR* values are shown.
* `-m METRIC [METRIC ...]`, `--metrics METRIC [METRIC ...]`: Specify the metrics
    to merge results for. By default all metrics that appear in filenames of
    found files will be merged. Note that this option only restricts the output,
    all files available are still read, however files not existing are not read.
* `-n NS [NS ...]`: The presence of this arguments specifies that only particular
  `n`-fault versions should be considered, where the parameters `a` etc. denote
  these `n`'s. When used with the `recurse` argument, only `.results` files in
  sub-directories named `<n>-fault` will be considered.
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
