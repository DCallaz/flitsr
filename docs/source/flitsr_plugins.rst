Creating ``flitsr`` plugins
===============================================================================

``flitsr`` can be easily extended with custom *plugins*. A *plugin* is an
extension to the ``flitsr`` framework which ``flitsr`` will automatically
discover if it is installed in the same *environment* as ``flitsr`` is (i.e. in
the same *Python virtual environment*). ``flitsr`` uses *entry points* to
discover plugins, using Python's `entry point specification <https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-package-metadata>`__
(see the link for more information).

To create a ``flitsr`` plugin, you can create a separate package with the
content of the plugin.

Example
-------------------------------------------------------------------------------

As an example, let's create a package called ``my-flitsr-plugin`` as a
``flitsr`` plugin.

.. note::
   There are no requirements on the naming convention of your plugin. You are
   free to name your plugin anything you like. We do however *advise* that you
   use "flitsr" in the name to distinguish it as a ``flitsr`` plugin.

The example package ``my-flitsr-plugin`` may have the following file
structure:::

  my-flitsr-plugin/
  ├─ pyproject.toml
  └─ my_flitsr_plugin/
     ├─ __init__.py
     └─ plugin.py

The ``pyproject.toml`` file might then look like this:

.. code-block:: toml
  :caption: pyproject.toml

  [build-system]
  requires = ["setuptools>=61.0"]
  build-backend = "setuptools.build_meta"

  [project]
  name = "my-flitsr-plugin"
  version = "0.0.1"
  authors = [
    {name="Some Guy", email="someguy@url.org"}
  ]
  description="A cool FLITSR plugin!"
  requires-python = ">=3.6"
  classifiers = [
    "Programming Language :: Python :: 3",
    "Operating System :: OS Independent",
    "Topic :: Software Development :: Debuggers",
    "Intended Audience :: Developers",
  ]
  dependencies = [
    'flitsr'
  ]

  [project.urls]
  Homepage = "https://example.com/my-flitsr-plugin"

  [project.entry-points.'flitsr.advanced']
  sliced = "my_flitsr_plugin.plugin:CustomAdvancedType"

  [project.entry-points.'flitsr.input']
  purefl_input = "my_flitsr_plugin.plugin:CustomInput"

This will create a ``flitsr`` plugin that has a custom :doc:`advanced type <adv_types>`
as well as a custom :doc:`input type <input_types>`. See below for all available
*entry points* for defining custom ``flitsr`` functionality.


``flitsr`` entry points
-------------------------------------------------------------------------------

``flitsr`` defines multiple *entry points* which can be used to extend
``flitsr`` functionality.

Advanced types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create an :doc:`advanced type <adv_types>` plugin, use the ``flitsr.advanced``
*entry point*:

.. code-block:: toml
  :caption: pyproject.toml

  [project.entry-points.'flitsr.advanced']
  test_adv = "my_flitsr_plugin.plugin:CustomAdvancedType"

Input types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create an :doc:`input type <adv_types>` plugin, use the ``flitsr.input``
*entry point*:

.. code-block:: toml
  :caption: pyproject.toml

  [project.entry-points.'flitsr.input']
  test_inp = "my_flitsr_plugin.plugin:CustomInput"
