Extending ``flitsr`` calculations
===============================================================================

By default, ``flitsr`` provides many of the most commonly used measures and
metrics for the evaluation of fault localization techniques. However, if there
are any other evaluation metrics you would like to use that are not yet
implemented, ``flitsr`` provides the functionality for you to easily create your
own in the form of *calculations*.

.. _calculation_format:

Calculation format
-------------------------------------------------------------------------------

A custom evaluation metric or *calculation* is simply a function which takes a
`~flitsr.tie.Ties` object and :py:class:`bool` for whether to collapse ambiguity
groups, as well as any other custom parameters, and returns any form of output
(usually a :py:class:`float`). The signature of a *calculation* function is:

.. py:function:: example_calculation(ties: Ties, collapse: bool, ...)

The function must be decorated with the `~flitsr.calculations.calculation`
decorator as specified below, which informs ``flitsr`` of the new calculation.

.. autofunction:: flitsr.calculations.calculation

An example *calculation* function using the above format would thus be:

.. code-block:: python

  from flitsr.calculations import calculation

  @calculation(print_name='custom_calc', desc='My custom calculation',
               'c-calc', 'custom-calculation')
  def example_calculation(ties: Ties, collapse: bool, my_param: str):
    ...

The above format would add a new ``flitsr`` calculation, which would have
command-line options ``--c-calc`` and ``--custom-calculation`` in the main
``flitsr`` application (with the help message ``"My custom calculation"``).
These options will take one :py:class:`str` argument, corresponding to
``my_param``. When this calculation is performed, the output produced by
``flitsr`` will be of the form ``"custom_calc: <output>"``.

Creating a calculation plugin
-------------------------------------------------------------------------------

To create a *calculation* :doc:`plugin <flitsr_plugins>`, use the
``flitsr.calculation`` entry point, for example:

.. code-block:: toml
  :caption: pyproject.toml

  [project.entry-points.'flitsr.calculation']
  my_calc = "my-package.custom_calc"

Where ``custom_calc`` is a python module containing the calculation function
using the `~flitsr.calculations.calculation` decorator.

Calculation parameters
-------------------------------------------------------------------------------

As noted in :ref:`calculation_format` above, a calculation can take any number
of other arbitrary parameters, which will be supplied by the command-line option
as arguments. ``flitsr`` will automatically detect any of these parameters in
the calculation function's signature, as well as any type annotations and defaults
given there. These type annotations and defaults will be used to construct the
command-line option arguments.

.. attention::
  Due to limitations in the `argparse` module, defaults given to the function
  signature will only be used if there is a single argument.

For parameters with simple primitive types (:py:class:`int`, :py:class:`str`,
:py:class:`bool`, :py:class:`float`, and :py:class:`~pathlib.Path`), ``flitsr``
will automatically convert the command-line agrument into the required type to
be given to the function.

For more complex types or conversions, or for parameters which may only take on
a finite set of values, the `~flitsr.calculations.parameter` decorator as given
below may be used.

.. autofunction:: flitsr.calculations.parameter

Using this decorator it is possible (using ``type``) to supply a custom function
which takes the string argument which would be given on the command-line, and
return the argument converted to be usable in your calculation. You may also
specify (using ``choices``), a collection of pre-defined choices which are valid
for the given parameter (cf. `flitsr.advanced.attributes.choices`).

.. note::
   As specified in the `argparse` documentation, choices are checked after any
   type conversions have been performed, so objects given by ``choices`` should
   match the type specified, as the function given by ``type`` will not be run
   on them.

Using the example given in :ref:`calculation_format` above, a example use of the
`~flitsr.calculations.parameter` decorator to specify pre-defined choices would
be:

.. code-block:: python

  from flitsr.calculations import calculation, parameter

  @parameter('my_param', choices=['choice1', 'choice2'])
  @calculation(print_name='custom_calc', desc='My custom calculation',
               'c-calc', 'custom-calculation')
  def example_calculation(ties: Ties, collapse: bool, my_param: str):
    ...
