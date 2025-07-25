Installation Instructions
===============================================================================

Requirements
-------------------------------------------------------------------------------

* ``python3``
* ``java`` (optional; used for parallel techniques)
* ``matplotlib`` (optional; used for evaluation plotting)

Installation
-------------------------------------------------------------------------------

Quick install
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install FLITSR, simply install as a python package using the following
command:

.. code-block::

    pip install flitsr

(Optional) See :ref:`Activate argument completion <install-arg-complete>`.

(Optional) See :ref:`Installing plotting features <install-plot>`.

.. _install-isolated:

Isolated installation (``pipx``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have too many dependencies in your main python installation, and would
rather prefer to have flitsr set up as a standalone tool instead of a python
package, you can install flitsr as a standalone tool using ``pipx``.

To do so, first ensure you have ``pipx`` installed. See
`this page <https://packaging.python.org/en/latest/guides/installing-stand-alone-command-line-tools/#installing-stand-alone-command-line-tools>`__
for details on installing ``pipx``.

Once ``pipx`` is installed, simply use the following command to install flitsr:

.. code-block::

   pipx install flitsr

(Optional) See :ref:`Activate argument completion <install-arg-complete>`.

(Optional) See :ref:`Installing plotting features <install-plot>`.

Install from source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Alternatively**, if you do not want to install flitsr using ``pip`` or ``pipx``,
you can install FLITSR manually from source. To do so, first clone this
repository using the command:

.. code-block::

   git clone https://github.com/DCallaz/flitsr.git

Build FLITSR as a python package
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

To build FLITSR as a python package and add it to your global python
installation (allowing importing of flitsr modules from python), use the
following commands:

.. code-block::

   cd flitsr
   python3 -m build
   pip install dist/flitsr*.whl

(Optional) See :ref:`Activate argument completion <install-arg-complete>`.

Build FLITSR as a standalone application
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
To build FLITSR as a standalone application, you may use ``pipx``. To do so, first
ensure you have ``pipx`` installed (see :ref:`install-isolated`).

Once ``pipx`` is installed, use the following commands to build and install
flitsr:

.. code-block::

   cd flitsr
   pipx install .

(Optional) See :ref:`Activate argument completion <install-arg-complete>`.

.. _install-arg-complete:

(Optional) Activate argument completion using ``argcomplete``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you would like all flitsr scripts to have TAB-like argument completion, you
will need to ensure ``argcomplete`` is set up.

To do so, run the following command after any of the above installation methods
to get autocompletion on the flitsr commands:

.. code-block::

   activate-global-python-argcomplete

.. _install-plot:

(Optional) Installing plotting features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you would like to use the flitsr framework to plot the percentage-at-n
figures, you will need to install the flitsr ``plot`` packaging extra. To do this,
use the following command:

.. code-block::

   pip install flitsr[plot]

You may also use ``flitsr[plot]`` to install the packaging extra using pipx.

