Transform spectra -- ``transform``
===============================================================================

If needed, a spectra in one format can be transformed into another format using
FLITSR's ``transform`` script. This script reads in the spectral input format
using FLITSR's usual input readers, and can print the resulting spectrum out to
any other supported format. For now this just includes TCM and GZoltar format
(see :doc:`input_types`). The command-line script has the following arguments:

``transform`` command line arguments
-------------------------------------------------------------------------------

.. argparse::
   :module: flitsr.transform
   :func: get_parser
   :prog: transform
   :nodescription:
