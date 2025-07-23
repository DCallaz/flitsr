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

.. toctree::
   base_tool
   :hidden:
   :caption: For developers

For researchers
-------------------------------------------------------------------------------

.. toctree::
   eval_framework
   :hidden:
   :caption: For researchers

Extending ``flitsr``
-------------------------------------------------------------------------------

.. toctree::
   :hidden:
   :caption: Extending flitsr
