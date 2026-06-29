Extending ``flitsr`` inputs
===============================================================================

``flitsr`` provides a number of :doc:`input_types` out-of-the-box, which cover a
range of use cases. However, if you have a different spectral format (say, the
output of a tool for a different programming language), you may also easily
extend ``flitsr`` to support this format as well.

To extend ``flitsr`` to support a different output format, you must create an
:class:`Input <flitsr.input.input_reader.Input>` class.

This class may either be created in the ``flitsr`` tool's ``input`` package, or
you may create a ``flitsr`` *pluin* using *entry points*. For details on how to
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

See the `~flitsr.input.Input` class for the structure that your custom input type
must extend. It is advised that you extend from either `~flitsr.input.DirInput`
or `~flitsr.input.FileInput` as a custom input type that reads in directories or
files respectively.

.. note::
   Your custom input type must implement all abstract methods, and may optionally
   implement any of the non-abstract, and non-final methods such as
   `~flitsr.input.Input.search_pattern`, `~flitsr.input.Input.write_spectrum`,
   and `~flitsr.input.Input.get_elem_separators`.

The main method to implement is the `Input._read_spectrum
<flitsr.input.Input._read_spectrum>` method as given here:

.. autofunction:: flitsr.input.Input._read_spectrum
