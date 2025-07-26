Input types
===============================================================================

``flitsr`` is a pure Spectrum-Based Fault Localization (SBFL) technique, and thus
only requires the collected coverage information from the execution of the test
suite over a system. ``flitsr`` currently supports two types of spectral input:
:ref:`TCM <input-tcm>` and :ref:`GZoltar <input-gzoltar>`. ``flitsr`` also
supports reading in a :ref:`ranking <input-ranking>`.

.. _input-tcm:

TCM format, taken from `"More Debugging in Parallel" <https://www.fernuni-hagen.de/ps/prjs/PD/>`__
--------------------------------------------------------------------------------------------------

.. code-block::

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

When using the ``method`` argument for FLITSR, ``<element name>`` must be of the format:
``<java package name>.<class name>:<method name>:<line number>``.

.. note::
   This format is slightly different than that described on the
   `TCM webpage <https://www.fernuni-hagen.de/ps/prjs/PD/>`__, for instance it
   does not require the exceptions for FAILED test cases and assumes a bug ID can
   be given for buggy elements. These differences are optional, as both this
   format **AND** the format given on the TCM webpage are supported, as well as
   any combination of the two. In this way, the format accepted is a more
   relaxed format.

.. _input-gzoltar:

GZoltar format, which can be generated using the `GZoltar tool <https://gzoltar.com/>`__
-----------------------------------------------------------------------------------------

This splits the coverage information into three separate files:

1. ``tests.csv``:
    .. code-block::
      :caption: tests.csv

      name,outcome,runtime,stacktrace
      <test name>,<status (PASS | FAIL)>[,<runtime>,<exception>]
      .
      .
      .

2. ``spectra.csv``:
    .. code-block::
      :caption: spectra.csv

      name
      <element name>[:<bugID>]
      .
      .
      .

    Where ``<element name>`` is of the format: ``<java package name>$<class
    name>#<method name>:<line number>``. Note that because of this restriction,
    FLITSR only supports statement-level coverage in GZoltar format.
3. ``matrix.txt``:
    The test and element numbering in this file refers to the indexing of the
    tests and elements in the ``tests.csv`` and ``spectra.csv`` files respectively.

    .. code-block::
      :caption: matrix.txt

      <element 0 executed in test 1> <element 1 executed in test 1> ...
      <element 0 executed in test 2> <element 1 executed in test 2>
      .
      .
      .

Input types API
-------------------------------------------------------------------------------

The API for the base `Input <flitsr.input.input_reader.Input>` class, as well as
all the implemented input types is given below:

.. autosummary::
   :recursive:
   :toctree: generated
   :template: custom-class-template.rst

   flitsr.input.input_reader.Input
   flitsr.input.tcm_input.TCM
   flitsr.input.gzoltar_input.Gzoltar

.. _input-ranking:

Ranking input
-----------------------------------------------------------------------------------------

Besides from the spectral formats, ``flitsr`` also supports reading in a
pre-generated *ranking* of a technique. There are currently two formats that
``flitsr`` supports: its own ``flitsr`` ranking format, and GZoltar ranking
format. The API for reading in rankings is given below:

.. toctree::

   read_ranking

Calling the `read_any_ranking <flitsr.read_ranking.read_any_ranking>` method
will automatically select the necessary ranking format based on the input file.
The structure for the two input formats are given below.

``flitsr`` ranking format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``flitsr`` ranking format has the following structure:

.. code-block::

   Faulty grouping: <score> [
     <element name> [(FAULT <bugId>)]
   ]
   .
   .
   .

GZoltar ranking format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The GZoltar ranking format has the following structure:

.. code-block::

   name;suspiciousness_value
   <element name>[:<bugId>];<score>
   .
   .
   .

Where ``<element name>`` is of the format: ``<java package name>$<class
name>#<method name>:<line number>``.

Creating your own input type
-------------------------------------------------------------------------------

``flitsr`` (and SBFL in general) is independant of the programming language or
spectrum input used, so it can support any arbitrary spectrum format from any
programming language. The spectrum formats given on this page are the ones
already integrated with FLITSR, however you can easily define your own input
type using *plugins*. See :doc:`input_ext` for more information.
