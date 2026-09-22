Extending ``flitsr`` ranking inputs
===============================================================================

``flitsr`` provides a number of :doc:`ranking_input_types` out-of-the-box, which
cover a range of use cases. However, if you have a different ranking format
(e.g., the ranking given by an external tool), you may also easily extend
``flitsr`` to support this format as well.

To extend ``flitsr`` to support a different ranking format, you must create an
:class:`RankingInput <flitsr.ranking_input.RankingInput>` class.

This class may either be created in the ``flitsr`` tool's ``ranking_input`` package,
or you may create a ``flitsr`` *pluin* using *entry points*. For details on how
to create a ``flitsr`` *plugin*, see :doc:`flitsr_plugins`. If creating a
``flitsr`` plugin, you may use the ``flitsr.ranking_input`` *entry point*, for
example:

.. code-block:: toml
  :caption: pyproject.toml

  [project.entry-points.'flitsr.ranking_input']
  test_rinput = "my-package.custom_ranking_input:CustomRanking"

Where ``CustomRanking`` is a custom ranking input type that inherits
:class:`RankingInput`.

.. note::
   The ``test_rinput`` variable name is not used by ``flitsr`` and thus can be
   arbitrary.

Abstract RankingInput class
-------------------------------------------------------------------------------

See the `~flitsr.ranking_input.RankingInput` class for the structure that your
custom ranking type must extend.

Your custom input type must implement all abstract methods from
`~flitsr.ranking_input.RankingInput`, including
`~flitsr.ranking_input.RankingInput._read_ranking` and
`~flitsr.ranking_input.RankingInput._check_format`, as given here:

.. autofunction:: flitsr.ranking_input.RankingInput._read_ranking

.. autofunction:: flitsr.ranking_input.RankingInput._check_format
