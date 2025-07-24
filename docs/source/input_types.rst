Input types
===============================================================================

FLITSR is a pure Spectrum-Based Fault Localization (SBFL) technique, and thus
only requires the collected coverage information from the execution of the test
suite over a system. FLITSR currently supports two input types:

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

GZoltar format, which can be generated using the `GZoltar tool <https://gzoltar.com/>`__
-----------------------------------------------------------------------------------------

This splits the coverage information into three separate files:

1. ``tests.csv``:
    .. code-block::

      name,outcome,runtime,stacktrace
      <test name>,<status (PASS | FAIL)>[,<runtime>,<exception>]
      .
      .
      .

2. ``spectra.csv``:
    .. code-block::

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

      <element 0 executed in test 1> <element 1 executed in test 1> ...
      <element 0 executed in test 2> <element 1 executed in test 2>
      .
      .
      .

Creating your own input type
-------------------------------------------------------------------------------

``flitsr`` (and SBFL in general) is independant of the programming language or
spectrum input used, so it can support any arbitrary spectrum format from any
programming language. The spectrum formats given on this page are the ones
already integrated with FLITSR, however you can easily define your own input
type using *plugins*. See :doc:`input_ext` for more information.
