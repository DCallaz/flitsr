.. flitsr documentation master file, created by
   sphinx-quickstart on Mon Jul 21 10:24:07 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

FLITSR
===============================================================================

``flitsr`` is an automatic fault-finding tool for programs with multiple faults.
The backbone of the ``flitsr`` tool is *Spectrum-Based Fault Localization*, a
fault-finding technology that uses a system's test suite to help find faults.
Included in the ``flitsr`` tool is the FLITSR (Fault Localization by Iterative
Test Suite Reduction) algorithm, a state-of-the-art technology that allows
``flitsr`` to find *multiple* faults at once.

The ``flitsr`` tool integrates with test suite information from both
`coverage.py <https://coverage.readthedocs.io/en/>`__ or `GZoltar <https://gzoltar.com/>`__.

Quick start
-------------------------------------------------------------------------------

To install FLITSR, simply install as a python package using the following command:

.. code-block:: bash

  pip install flitsr

For more detailed instructions, see :doc:`install`.

.. toctree::
   install
   :hidden:
   :caption: General

For developers
-------------------------------------------------------------------------------

``flitsr`` is primarily a debugging tool to assist developers in finding faults
in their code. If you are looking for information on using ``flitsr`` as a
debugging tool, the following sections are for you:

.. toctree::
   base_tool
   input_types
   adv_types
   api
   :caption: For developers
   :maxdepth: 1

For researchers
-------------------------------------------------------------------------------

Included in ``flitsr`` is also the ``flitsr`` *evaluation framework*, which
contains functionality necessary to run large-scale SBFL experiments for
researchers. If you are looking on how to use the ``flitsr`` evaluation
framework to run experiments, see the following sections:

.. toctree::
   eval_framework
   merging
   plotting
   :caption: For researchers
   :maxdepth: 1

Extending ``flitsr``
-------------------------------------------------------------------------------

``flitsr`` has been designed to be as versatile as possible, allowing changes
and additions to almost every aspect of its functionality. The following
sections provide information on what can be extended in ``flitsr`` and how:

.. toctree::
   flitsr_plugins
   input_ext
   adv_type_ext
   :caption: Extending flitsr
   :maxdepth: 1
