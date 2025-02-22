Collaborative Literature Reviews
========================================

.. figure:: https://raw.githubusercontent.com/CoLRev-Ecosystem/colrev/main/docs/figures/logo_small.png
   :width: 400
   :align: center
   :alt: Logo

CoLRev is an open-source environment for collaborative literature reviews. It integrates with differerent synthesis tools, takes care of the data, and facilitates Git-based collaboration.

To accomplish these goals, CoLRev advances the design of review technology at the intersection of methods, design, cognition, and community building.
The following features stand out:

- An open and extensible environment based on data and process standards
- Builds on git and its transparent collaboration model for the entire literature review process
- Offers a self-explanatory, fault-tolerant, and configurable user workflow
- Operates a model for data quality, content curation, and reuse
- Provides validate and undo operations
- Enables typological and methodological pluralism throughout the process (`in-progress <https://github.com/CoLRev-Environment/colrev/issues/110>`_)

Please consult the :doc:`statements of development status </dev_docs/dev_status>`. A brief overview presented at ESMARConf2023 is available on `YouTube <https://www.youtube.com/watch?v=yfGGraQC6vs>`_.

Getting started
---------------------------------------

After installing `git <https://git-scm.com/>`_ and `docker <https://www.docker.com/>`_ (Docker is optional but recommended):

.. code-block::

   # Install
   pip install colrev

   # ... and start with the main command
   colrev status

The CoLRev environment supports for the whole literature review process:

.. figure:: ../figures/figure-docs.png
   :width: 600
   :align: center
   :alt: Workflow cycle


Completing a literature review should be as simple as running the following commands:

.. code-block::

   # Formulate the objectives, initialize the project, specify the review type
   colrev init

   # Store search results in the data/search directory
   # Load, prepare, and deduplicate the metadata reocrds
   colrev retrieve

   # Conduct a prescreen
   colrev prescreen

   # Get and prepare the PDFs
   colrev pdfs

   # Conduct a screen based on PDFs
   colrev screen

   # Complete the forms of data analysis and synthesis, as specified in the settings
   colrev data

Further information is provided in the :doc:`documentation <index>`.
The manual explains how to use the functionality of CoLRev when conducting a literature review. It covers the user workflow, the processing operations, as well as collaboration and curation.
It does not explain the design and architecture of CoLRev, which are covered in the :doc:`colrev framework </foundations/cep/cep001_framework>` and the :doc:`API reference </dev_docs/api>`.
Our goal is to provide a manual that is self-contained. Yet, it can help to be familiar with the basics of git - for example, by catching up with one of the interactive and free tutorials available online (`tutorial <https://learngitbranching.js.org/>`_).

The manual is available under the `Creative Commons Attribution-NonCommercial-NoDerivs 3.0 License <https://creativecommons.org/licenses/by-nc-nd/3.0/us/>`_ and endorses the `Code of Conduct <https://www.contributor-covenant.org/version/2/0/code_of_conduct/>`_ for contributions.


.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Manual

   manual/operations
   manual/workflow
   manual/problem_formulation
   manual/metadata_retrieval
   manual/metadata_prescreen
   manual/pdf_retrieval
   manual/pdf_screen
   manual/data
   manual/cli
   manual/collaboration
   manual/packages
   manual/appendix

.. toctree::
   :hidden:
   :caption: Developer documentation
   :maxdepth: 1

   dev_docs/setup
   dev_docs/packages
   dev_docs/dev_status
   dev_docs/api
   Github repository <https://github.com/CoLRev-Environment/colrev>
   PyPI <https://pypi.org/project/colrev/>

.. toctree::
   :hidden:
   :caption: Governance
   :maxdepth: 1

   foundations/cep
   foundations/credits
   foundations/about
