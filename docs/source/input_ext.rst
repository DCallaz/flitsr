Extending ``flitsr`` inputs
===============================================================================

``flitsr`` provides a number of :doc:`input_types` out-of-the-box, which cover a
range of use cases. However, if you have a different spectral format (say, the
output of a tool for a different programming language), you may also easily
extend ``flitsr`` to support this format as well.

To extend ``flitsr`` to support a different output format, you must create an
:class:`Input <flitsr.input.input_reader.Input>` class.

This class may either be created in the ``flitsr`` tools ``input`` package, or you
may create a ``flitsr`` *pluin* using *entry points*. For details on how to
create a ``flitsr`` *plugin*, see :doc:`flitsr_plugins`. If creating a
``flitsr`` plugin, you may use the ``flitsr.input`` *entry point*, for example:

.. code-block:: toml
  :caption: pyproject.toml

  [project.entry-points.'flitsr.input']
  test_input = "my-package.custom_input:CustomInput"

Where ``CustomInput`` is a custom input type that inherits
:class:`Input <flitsr.input.input_reader.Input>`.

.. note::
   The ``test_input`` variable name is not used by ``flitsr`` and thus can be
   arbitrary.

Abstract Input class
-------------------------------------------------------------------------------

The abstract :class:`Input <flitsr.input.input_reader.Input>` class that your
custom input type must extend has the following structure.

.. note::
   Your custom input type must implement all abstract methods, and may optionally
   implement the :meth:`write_spectrum <flitsr.input.input_reader.Input.write_spectrum>`,
   and :meth:`get_elem_separators <flitsr.input.input_reader.Input.get_elem_separators>` methods.

.. autoclass:: flitsr.input.input_reader.Input
   :members:
