``flitsr`` advanced types
===============================================================================

The ``flitsr`` framework supports the use of advanced techniques which operate
over the spectra or rankings. Currently there are three types of advanced types,
:ref:`adv-clusters`, :ref:`adv-refiners` and :ref:`adv-rankers`. Each of these
``flitsr`` advanced types is a template which specifies a class of techniques
that take a certain input(s) and return a certain output.

.. note::
  You can implement any of the ``flitsr`` advanced types by creating a :doc:`flitsr
  plugin <flitsr_plugins>`. For more information, see :doc:`adv_type_ext`.

.. _adv-clusters:

Clusters
-------------------------------------------------------------------------------

`Cluster`\s are the first type of ``flitsr`` advanced type, and operate directly
on the spectrum, returning multiple spectra in return. They are the first
advanced type to be run in the flow of ``flitsr``\s execution.

The `Cluster <flitsr.advanced.cluster.Cluster>` type is only required to define
one method, `cluster <flitsr.advanced.cluster.Cluster.cluster>`, which takes the
input `Spectrum <flitsr.spectrum.Spectrum>` (along with some other useful
parameters), and returns a collection of spectra decomposed from the original.

Various implementations of the `Cluster <flitsr.advanced.cluster.Cluster>` type
may implement the decomposition differently, which constitute novel techniques.

Incorporated in the ``flitsr`` framework are the collection of `Parallel Debugging
<https://doi.org/10.1109/ISSRE.2014.29>`__  techniques, which decompose the
spectrum according to the techniques described in `"More Debugging in Parallel"
<https://doi.org/10.1109/ISSRE.2014.29>`__. See the :ref:`--parallel <flitsr-parallel>`
command line option for usage of these techniques.

The API for a `Cluster <flitsr.advanced.cluster.Cluster>` type, as well as any
implemented ``Cluster``\s are given below:

.. autosummary::
   :recursive:
   :toctree: generated
   :template: custom-class-template.rst

   flitsr.advanced.cluster.Cluster
   flitsr.advanced.parallel.Parallel

.. _adv-refiners:

Refiners
-------------------------------------------------------------------------------

The second advanced type that is run by ``flitsr`` is a `Refiner
<flitsr.advanced.refiner.Refiner>`. `Refiner <flitsr.advanced.refiner.Refiner>`\s
take a ``flitsr`` spectrum, manipulate and extend it, and return a modified
spectrum. `Refiner <flitsr.advanced.refiner.Refiner>`\s are useful for extending
a spectrum with additional information before using it to form a `Ranking
<flitsr.ranking.Ranking>` with SBFL techniques.

Like the `Cluster <flitsr.advanced.cluster.Cluster>` type, `Refiner
<flitsr.advanced.refiner.Refiner>` types need only implement one method: `refine
<flitsr.advanced.refiner.Refiner.refine>`, which takes a spectrum and returns a
modified spectrum.

Currently there are no `Refiner <flitsr.advanced.refiner.Refiner>`\s implemented
directly in the ``flitsr`` framework. However you can still :doc:`create your
own <adv_type_ext>`.

The API for a `Refiner <flitsr.advanced.refiner.Refiner>` type is given below:

.. autosummary::
   :recursive:
   :toctree: generated
   :template: custom-class-template.rst

   flitsr.advanced.refiner.Refiner

.. _adv-rankers:

Rankers
-------------------------------------------------------------------------------

The last, and possibly most useful ``flitsr`` advanced type is a `Ranker
<flitsr.advanced.ranker.Ranker>`. A `Ranker <flitsr.advanced.ranker.Ranker>`
takes a `Spectrum <flitsr.spectrum.Spectrum>` and uses the information from the
Spectrum to rank the elements, forming a `Ranking <flitsr.ranking.Ranking>`.

As before, there is only one method to implement, the `rank
<flitsr.advanced.ranker.Ranker.rank>` method which takes a spectrum and SBFL base
metric and returns a `Ranking <flitsr.ranking.Ranking>`.

The ``flitsr`` framework currently has four defined `Ranker
<fflitsr.advanced.ranker.Ranker>` types, which are :ref:`sbfl <flitsr-sbfl>`,
:ref:`flitsr <flitsr-flitsr>`, :ref:`multi <flitsr-multi>` and :ref:`artemis
<flitsr-artemis>`.

The simplest of these is the :ref:`sbfl <flitsr-sbfl>` technique, which simply
returns the `Ranking <flitsr.ranking.Ranking>` formed by the SBFL base metric
given.

The :ref:`flitsr <flitsr-flitsr>` and :ref:`multi <flitsr-multi>` techniques
implement the FLITSR and FLITSR*/FLITSR MULTI algorithms as described in
`"FLITSR: Improved Spectrum-Based Localization of Multiple Faults by Iterative
Test Suite Reduction" <https://doi.org/10.1145/3745027>`__. These techniques
improve the effectiveness of the SBFL techniques for programs with *multiple
faults*. The :ref:`flitsr <flitsr-flitsr>` `Ranker <flitsr.advanced.ranker.Ranker>`
is the default when running the :ref:`flitsr command line tool <flitsr-tool>`.

Finally the :ref:`artemis <flitsr-artemis>` techniques implement the ARTEMIS
algorithm, as described in `"Augmenting Automated Spectrum Based Fault
Localization For Multiple Faults" <https://doi.org/10.24963/ijcai.2023/350>`__.
The technique is also designed to improve SBFL effectiveness in the presence of
multiple faults.

The API for a `Ranker <flitsr.advanced.ranker.Ranker>` as well as all
`Ranker <flitsr.advanced.ranker.Ranker>`\s in ``flitsr`` are given below:

.. autosummary::
   :recursive:
   :toctree: generated
   :template: custom-class-template.rst

   flitsr.advanced.Config
   flitsr.advanced.ranker.Ranker
   flitsr.advanced.sbfl.SBFL
   flitsr.advanced.flitsr.Flitsr
   flitsr.advanced.flitsr.Multi
   flitsr.advanced.artemis_wrapper.Artemis

