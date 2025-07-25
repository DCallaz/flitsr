Creating custom drivers
===============================================================================

The ``flitsr`` framework provides many extendable aspects which allow you to
customize its behaviour. However in some cases you may wish to change ``flitsr``\s
execution flow beyond what you can customize using the other extensions. If this
is the case, you can create a *custom driver*.

A driver is essentially a method which controls the execution of ``flitsr``.
``flitsr`` by default uses the main driver which facilitates reading in the
spectrum, running techniques and producing results, which is what is run when
using the ``flitsr`` and ``run_all`` commands. Since ``flitsr`` is also
designed to be usable as a :doc:`python package <api>`, you can easily define
your own execution flow for ``flitsr``, which we call a *driver*.

If you would like to use your ``flitsr`` *driver* within the ``run_all``
command, you must register it as a *driver* using the ``flitsr.driver`` entry
point, for example:

.. code-block:: toml
  :caption: pyproject.toml

  [project.entry-points.'flitsr.driver']
  dummy_driver = "my-package.custom_driver"

where ``custom_driver`` is the name of a python module (i.e. ``custom_driver.py``)
that contains a ``main`` method. The main method must use the following API:

.. py:function:: main(args: Optional[List[str]] = None)

   Run the custom driver.

   :param args: The command line options.
   :type args: List[str] or None
