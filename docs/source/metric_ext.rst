Extending ``flitsr`` SBFL metrics
===============================================================================

``flitsr`` comes pre-loaded with a large number of SBFL metrics implemented
which can be used to create SBFL rankings. If, however, you would like to run an
SBFL metric which is not implemented, you can easily add it to ``flitsr`` using
the ``flitsr.metric`` plugin.

To extend ``flitsr`` to support a new SBFL metric, you must create a function
which takes the summary of counts for each element used in all SBFL metrics, and
return a suspiciousness score (as a `float`). The function must take four `int`
arguments representing ``ef`` (number of failing tests the element is executed
in), ``tf`` (total number of failing tests), ``ep`` (number of passing tests the
element is executed in), and ``tp`` (total number of passing tests) in that order.

As an example, the ochiai metric can be implemented with the following function:

.. code-block:: python
  :caption: custom_metric.py

  def ochiai_metric(ef: int, tf: int, ep: int, tp: int) -> float:
      denominator = math.sqrt(tf * (ef + ep))
      if (ef == 0):
          return 0.0
      elif (denominator == 0):
          return Suspicious.inf
      return ef/denominator


To expose the function you created such as the one above to the ``flitsr`` tool,
you must create a ``flitsr`` *plugin* using *entry points*. For more details on
how to create a ``flitsr`` *plugin*, see :doc:`flitsr_plugins`. For SBFL metric
plugins, you may use the ``flitsr.metric`` *entry point*, which is added to your
plugin package's ``pyproject.toml`` file as follows:

.. code-block:: toml
  :caption: pyproject.toml

  [project.entry-points.'flitsr.metric']
  ochiai = "my-package.custom_metric:ochiai_metric"

.. note::
   The ``ochiai`` variable name is used by ``flitsr`` as the name of the metric,
   not the function name.
