Plotting figures -- ``percent_at_n``
===============================================================================

The ``flitsr`` evaluation framework supports automatic plotting of
percentage-at-n figures, using the results of the :ref:`merge -p option<merge-p>`.
To plot these figures, use the ``percent_at_n plot`` command.


``percent_at_n plot`` command line arguments
-------------------------------------------------------------------------------

.. argparse::
   :module: flitsr.percent_at_n
   :func: get_parser
   :prog: percent_at_n plot
   :path: plot
   :nodescription:

