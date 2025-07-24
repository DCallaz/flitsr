Merging results - ``merge``
===============================================================================

Once ``.results`` files have been generated using the :doc:`run_all </eval_framework>`,
you can then merge these into useful statistics using the :py:mod:`flitsr.merge`
command.

``merge`` command line arguments
-------------------------------------------------------------------------------

.. argparse::
  :module: flitsr.merge
  :func: get_parser
  :prog: merge
  :nodescription:

  -p --perc@n : @before
    .. _merge-p:
