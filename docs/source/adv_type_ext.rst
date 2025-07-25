Extending ``flitsr`` advanced types
===============================================================================

``flitsr`` provides a number of techniques implemented as :doc:`advanced types <adv_types>`,
which you can employ when using ``flitsr``. However ``flitsr`` also provides the
functionality for you to easily create your own advanced type, if you would like
to extend ``flitsr`` to support another technique.

To create a new technique for an advanced type, you will need to define a class
which extends a current advanced type base class. The available advanced types
are given in :doc:`adv_types`. You would create your advanced type either within
the ``advanced`` package of ``flitsr``, or (more likely) create a separate
:doc:`plugin <flitsr_plugins>`. Creating this concrete implementation of an
advanced type using either of these two ways will allow ``flitsr`` to
automatically discover and make available your advanced type.

To create an advanced type :doc:`plugin <flitsr_plugins>`, use the
``flitsr.advanced`` entry point, for example:

.. code-block:: toml
  :caption: pyproject.toml

  [project.entry-points.'flitsr.advanced']
  adv_mthd = "my-package.custom_adv_type:CustomTechnique"

Where ``CustomTechnique`` is a custom advanced type that inherits one of the
:doc:`advanced types <adv_types>`.

Since custom techniques will have various different algorithms and potentially
other input, ``flitsr`` makes it easy to customize :doc:`advanced types
<adv_types>` by providing some helpful structure and functions for advanced
types.

Passing input parameters -- the ``__init__`` method
-------------------------------------------------------------------------------

``flitsr`` allows any advanced type to take additional inputs which they can use
within their implementation. To do this, ``flitsr`` analyzes the signature of
the ``__init__`` method of *any* advanced type, and processes the parameters of
this method, making them **automatically** available as command line parameters,
which ``flitsr`` will provide when calling the advanced type.

As an example, let's use the ``parallel`` advanced type. The ``__init__`` method
of the ``parallel`` advanced type is as follows:

.. code-block:: python
   :caption: advanced/parallel.py

    def __init__(self, parType: str = 'msp'):
        self.parType = parType

This advanced type takes one additional parameter, ``parType`` which has a type
hint indicating it is a ``str``. It also has a default value set, which is
``'msp'``.

``flitsr`` automatically processes this advanced types ``__init__`` method, and
extracts this information, automatically producing the command line option
:ref:`--parallel-parType <flitsr-parallel-parType>`. The command line option is
automatically created to have a parameter with type ``str``, which has the
default value of ``'msp'``.

``flitsr`` uses `argparse <https://docs.python.org/3/library/argparse.html>`__
for its command line processing, which will automatically support conversion to
any primitive type. For conversion to a non-primitive type, you may implement a
method named ``_<param>`` in your advanced type class, where ``<param>`` is the
name of the ``__init__`` parameter to convert, which takes a string and converts
it to your custom type. For example, if your technique takes a parameter ``my_date``,
which is a date in the format ``'Jun 1 2005  1:33PM'``, you could specify the
function:

.. code-block:: python

   def _my_date(date_str : str):
       from datetime import datetime
       return datetime.strptime(date_str, '%b %d %Y %I:%M%p').date()

This would be automatically discovered by ``flitsr``, and will be passed to
``argparse`` to be used to convert the parameter to a date object.

Advanced type attributes -- ``existing``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some cases, you would like to define a parameter to your function that takes
the value of an argument already passed to ``flitsr``, instead of defining a new
command line argument. For example, you might want your technique to use the
``--tiebrk`` argument to ``flitsr``, with which the user specifies how to break
ties throughout ``flitsr``. To include already defined arguments in the
parameters of your advanced type, ``flitsr`` provides the `existing
<flitsr.advanced.attributes.existing>` decorator function which can be applied to
the ``__init__`` method. The decorator has the following usage:

.. autofunction:: flitsr.advanced.attributes.existing

Using the example of the ``--tiebrk`` option, you would do the following:

.. code-block:: python

  @existing('tiebrk')
  def __init__(self, tiebrk: Tiebrk):
      self.tiebrk = tiebrk

``flitsr`` would then automatically fill that parameter with the value of the
``--tiebrk`` command line argument when instantiating your advanced type.


Advanced type attributes -- ``choices``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For some parameters, you may also want to specify a number of pre-defined
choices for a particular parameter. ``flitsr`` allows you to do this using the
`choices <flitsr.advanced.attributes.choices>` decorator, which can be applied
to the ``__init__`` method, similar to the `existing
<flitsr.advanced.attributes.existing>` decorator. The `choices
<flitsr.advanced.attributes.choices>` decorator has the following usage:

.. autofunction:: flitsr.advanced.attributes.choices

As an example, the ``parType`` parameter of our ``--parallel`` example has four
pre-defined strings that it accepts: ``bdm``, ``msp``, ``hwk``, and ``vwk``. To
define this set of choices for the ``parallel`` advanced type, we would do the
following:

.. code-block:: python

  @choices('parType', ['bdm', 'msp', 'hwk', 'vwk'])
  def __init__(self, parType: str = 'msp'):
      self.parType = parType

This is the implementation used for the ``__init__`` method of the ``parallel``
technique, from which ``flitsr`` automatically creates the
:ref:`--parallel-parType <flitsr-parallel-parType>` command line option.

Advanced type attributes -- ``print_name``
-------------------------------------------------------------------------------

The last type of helper method that ``flitsr`` provides is the `print_name
<flitsr.advanced.attributes.print_name>` decorator. This is a *class level*
decorator, that can be used on an advanced type class to define a different name
to be used when ``flitsr`` prints results to output files. This name will then
appear in file names and :doc:`merged result files <merging>`. The usage of this
decorator is as follows:

.. autofunction:: flitsr.advanced.attributes.print_name

An example of the usage is for the ``sbfl`` advanced type in ``flitsr``. For
this advanced type, we would like a different name to be used when printing out
results, namely ``'base'`` instead of ``'sbfl'``. The ``sbfl`` class is thus
defined as:

.. code-block:: python

   @print_name('base')
   class SBFL(Ranker):
       ...
