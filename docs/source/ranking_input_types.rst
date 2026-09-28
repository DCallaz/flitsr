Ranking input
===============================================================================

Besides from the spectral formats, ``flitsr`` also supports reading in a
pre-generated *ranking* of a technique. There are currently three formats that
``flitsr`` supports: its own ``flitsr`` ranking format, GZoltar ranking
format, and TransferFL ranking format. The API for reading in rankings is given below:

.. autosummary::
   :recursive:
   :toctree: generated
   :template: custom-class-template.rst

   flitsr.ranking_input.RankingInput
   flitsr.ranking_input.FlitsrRanking
   flitsr.ranking_input.GzoltarRanking
   flitsr.ranking_input.TransferFLRanking

Calling the `RankingInput.read_any_ranking <flitsr.ranking_input.RankingInput.read_any_ranking>`
method will automatically select the necessary ranking format based on the input
file. The structure for each input format is given below.

``flitsr`` ranking format
-------------------------------------------------------------------------------

The ``flitsr`` ranking format has the following structure:

.. code-block::

   Faulty grouping: <score> [
     <element name> [(FAULT <bugId>)]
   ]
   .
   .
   .

Where ``<element name>`` is in the format: "``<path name>|<file name>|<method
name>|<line number>``", where any of the components are optional.

GZoltar ranking format
-------------------------------------------------------------------------------

The GZoltar ranking format has the following structure:

.. code-block::

   name;suspiciousness_value
   <element name>[:<bugId>];<score>
   .
   .
   .

Where ``<element name>`` is of the format: "``<java package name>$<class
name>#<method name>:<line number>``".

TransferFL ranking format
-------------------------------------------------------------------------------

The TransferFL ranking format has the following structure:

.. code-block::

   <element name> <score>[ <bugId>]
   .
   .
   .

Where ``<element name>`` is of the format: "``<package/path name>.<class/file
name>@<method name>@<line number>``".


Creating your own ranking input type
-------------------------------------------------------------------------------

The ranking input types given on this page are the ones already integrated in
FLITSR, however, ``flitsr`` allows you to define your own ranking input type
using *plugins*. See :doc:`ranking_input_ext` for more information.
