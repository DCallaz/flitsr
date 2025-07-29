# FLITSR
A python implementation of the FLITSR fault localization tool for multiple
faults.

For the full documentation, see the [Read the Docs
page](https://flitsr.readthedocs.io), and for the source code, see the [GitHub
repository](https://github.com/DCallaz/flitsr).

## Setup
### Requirements
* `python3` (> `3.6`)
* `java` (optional; used for parallel techniques)
* `matplotlib` (optional; used for evaluation plotting)
### Installation
#### Quick install
To install FLITSR, simply install as a python package using the following
command:
```
pip install flitsr
```

For more detailed installation instructions, see [Installation
Instructions](https://flitsr.readthedocs.io/en/latest/install.html) in the
documentation.

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

More advanced options and outputs are described in the
[documentation](https://flitsr.readthedocs.io/en/latest/base_tool.html).

### Running evaluation
To run the full evaluation on FLITSR, simply use the command:
```
run_all [-t [<extension>]/-g]
```
in the top level directory for the dataset. If the `-t` option is given (with an
optional file extension), then the TCM format is assumed, otherwise if the `-g`
option is given, Gzoltar format is assumed.

See the [documentation](https://flitsr.readthedocs.io/en/latest/eval_framework.html)
for more information.
