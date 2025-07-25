Using the ``flitsr`` API
===============================================================================

The ``flitsr`` framework is not only available as a command line tool, but is
also designed for usage as a Python package via the ``flitsr`` API.

For more information on the API functionality provided by ``flitsr``, see the
:ref:`api` below. Also have a look at the :ref:`example` for tips on how to use
``flitsr`` as a Python package.

.. _api:

API
-------------------------------------------------------------------------------

.. autosummary::
   :recursive:
   :toctree: generated
   :template: custom-module-template.rst

   flitsr.spectrumBuilder
   flitsr.spectrum
   flitsr.ranking
   flitsr.tie

.. _example:

Example
-------------------------------------------------------------------------------

Let's look at an example of using ``flitsr`` as a Python package. You can of
course use ``flitsr`` in any way you wish, but we will focus on the main
functionality here. In particular, this example will demonstrate a simple
example of running the Ochiai SBFL technique over an example spectrum.

To start, let's read in the `Spectrum <flitsr.spectrum.Spectrum>`. We'll use the
:doc:`example_spectrum`, which is located at ``./example_spectrum.tcm``.

.. code-block:: python

  from flitsr.input.input_reader import Input
  spectrum = Input.read_in('./example_spectrum.tcm', False)

This will use the TCM format to read in the Spectrum, and store the resulting
``flitsr`` `Spectrum <flitsr.spectrum.Spectrum>` in our ``spectrum`` variable.

.. note::

   The `Spectrum <flitsr.spectrum.Spectrum>` contains a variety of useful methods
   to retrieve information about the tests, elements and coverage between them.
   Have a look at the `Spectrum <flitsr.spectrum.Spectrum>` API for more
   information.

Once the spectrum has been read in, we'll want to run the Ochiai SBFL algorithm
over it to produce a `Ranking <flitsr.ranking.Ranking>`. The SBFL technique
takes the spectrum as well as the metric we want to use; in this case, Ochiai.
To do this, let's use the following code:

.. code-block:: python

  from flitsr.advanced.sbfl import SBFL
  ranking = SBFL().rank(spectrum, 'ochiai')

In the above, we instantiated an instance of the ``SBFL`` advanced type, which we
then used this instance to rank the spectrum using the ``'ochiai'`` formula,
producing a `Ranking <flitsr.ranking.Ranking>`.

We can then use this `Ranking <flitsr.ranking.Ranking>` to inspect the elements
ranked as most suspicious by the FLITSR technique using our Ochiai metric. Let's
have a look at what the top-ranked group is:

.. code-block:: python

  print(ranking[0].score, ranking[0].entity)
  >>> 0.6123724356957946 G6 ([l12])

As we can see, the top-ranked group is G6, with the element l12. It has a
suspiciousness score of around ``0.6``. Let's look at the next most suspicious:

.. code-block:: python

  print(ranking[1].score, ranking[1].entity)
  >>> 0.42640143271122083 G4 ([l9 (FAULT 1)])

This is group G4, with element l9, which we see pertains to fault 1.

.. note::

   This fault information will not be available for real-world examples where
   the fault is unknown. It is only available for examples (like this one) where
   the faults have been specified.

Let's look into what failures this fault is executed in. To do that, we'll use
some helper functions in the `Spectrum <flitsr.spectrum.Spectrum>`:

.. code-block:: python

  print(spectrum.get_tests(ranking[1].entity, only_failing=True))
  >>> {c5, c3, c4, c2}

Element l9 could thus be the cause for these four failing tests: ``c2``, ``c3``,
``c4`` and ``c5``.

There are many other useful features to ``flitsr``, and we encourage you to look
at the :ref:`api` for more information.
