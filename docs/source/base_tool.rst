Base tool - ``flitsr``
===============================================================================

This section describes usage instructions for developers wishing to use
``flitsr`` to assist in debugging programs.

.. _flitsr-tool:

``flitsr`` command line arguments
-------------------------------------------------------------------------------

.. argparse::
   :module: flitsr.args
   :func: get_parser
   :prog: flitsr
   :nodescription:

   Spectrum refiner techniques : @after
     See :doc:`adv_types` for more information on ``flitsr`` advanced types.

   Clustering techniques : @after
     See :doc:`adv_types` for more information on ``flitsr`` advanced types.

   --parallel : @before
     .. _flitsr-parallel:

   --parallel-parType : @before
     .. _flitsr-parallel-parType:

   Ranking techniques : @after
     See :doc:`adv_types` for more information on ``flitsr`` advanced types.

   --sbfl : @before
     .. _flitsr-sbfl:

   --flitsr : @before
     .. _flitsr-flitsr:

   --multi : @before
     .. _flitsr-multi:

   --artemis : @before
     .. _flitsr-artemis:
