Package development
=====================

CoLRev packages are Python packages that extend CoLRev by relying on its shared data structure, standard process, and common interfaces.
Packages can support specific endpoints (e.g., `search_source`, `prescreen`, `pdf-get`) or provide complementary functionalities (e.g., for ad-hoc data exploration and visualization).

The following guide explains how to develop built-in packages, i.e., packages that reside in the `packages` directory.

..
    CoLRev comes with batteries included, i.e., a reference implementation for all steps of the process. At the same time you can easily include other packages or custom scripts (batteries are swappable). Everything is specified in the settings.json (simply add the package/script name as the endpoint in the ``settings.json`` of the project):

    .. code-block:: diff

    ...
        "screen": {
            "criteria": [],
            "screen_package_endpoints": [
                {
    -             "endpoint": "colrev.colrev_cli_screen"
    +             "endpoint": "custom_screen_script"
                }
            ]
        },
        ...

  * In case of external packages, you need to register it by updating ``packages.json`` but it's not required for built-in packages.
  Examples
  ========
  - `colrev-asreview <https://github.com/CoLRev-Environment/colrev-asreview>`_
  * Register the package to the cloned CoLRev by editing the ``colrev/packages/packages.json`` file e.g.:
    ..  code-block:: diff
        ...
          {
              "module": "colrev",
              "url": "https://github.com/CoLRev-Environment/colrev"
          },
        + {
        +     "module": "colrev_asreview",
        +     "url": "https://github.com/CoLRev-Environment/colrev-asreview"
        + }
    For development and testing purpose it’s convenient to fork the CoLRev repository, setup a venv with the forked repository, and work on the package. Once the package is developed, and working as expected, you can make a pull request to original repository to register your package.

    Following steps might be a good starting point.

    * Fork and clone CoLRev
    * Setup a virtualenv, all the followings steps assumes the same virtualenv used throughout
    * Install the cloned CoLRev using pip command ``pip install -e /path/to/cloned/colrev``

      .. note::

          ``-e`` allows editable installation. Any changes made will be available immediately

    * Create the package repository e.g.: https://github.com/CoLRev-Environment/colrev-asreview

      .. note::

          You can simply use `this repository <https://github.com/CoLRev-Environment/colrev-asreview>`_ as the ground for your package

    * `Add <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics>`_ the ```colrev-packages``` `topic tag on GitHub <https://github.com/topics/colrev-package>`_ to allow others to find and use your work.

Package structure
------------------

A package contains the following files and directories:

   ::

    ├── pyproject.toml
    ├── README.md
    ├── src
    │   ├── __init__.py
    │   ├── package_functionality.py

..
       ├── .pre-commit-config.yaml
   .. note::

      The``.pre-commit-config.yaml`` should be copied from the CoLRev repo to ensure CoLRev’s coding standards

Package metadata: pyproject.toml
--------------------------------

The package metadata is stored in the ``pyproject.toml`` file. The metadata is used by the CoLRev to identify the package and its dependencies. The metadata should include the following fields:

   ::

    [project]
    name = "colrev.abi_inform_proquest"
    description = "CoLRev package for abi_inform_proquest"
    version = "0.1.0"
    authors = [
        { name = "Gerit Wagner", email = "gerit.wagner@uni-bamberg.de" }
    ]
    documentation = "README.md"
    colrev_doc_link = "README.md"

    [tool.colrev]
    dev_status = "maturing"
    search_source = "colrev.packages.abi_inform_proquest.src.package_functionality:ABIInformProQuestSearchSource"

.. note::

          The `tool.colrev` section contains the :doc:`dev_status </dev_docs/dev_status>` and the endpoints (e.g., `search_source`).

Implementing endpoints
-------------------------

Endpoints allow packages to implement functionality that can be called in the :doc:`standard process </manual/operations>` if users register the endpoint in the `settings.json` of a project.

To implement an endpoint, the `tool.colrev` section of `pyproject.toml` must provide a reference to the endpoint class which implements the respective :doc:`interfaces </dev_docs/packages/package_interfaces>`. The reference is a string that contains the module path and the class name of the endpoint. The module path is relative to the package directory.

The following endpoint - interface pairs are available:

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Endpoint
     - Interface
   * - review_type
     - `ReviewTypeInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.ReviewTypeInterface>`_
   * - search_source
     - `SearchSourceInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.SearchSourceInterface>`_
   * - prep
     - `PrepInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.PrepInterface>`_
   * - prep_man
     - `PrepManInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.PrepManInterface>`_
   * - dedupe
     - `DedupeInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.DedupeInterface>`_
   * - prescreen
     - `PrescreenInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.PrescreenInterface>`_
   * - pdf_get
     - `PDFGetInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.PDFGetInterface>`_
   * - pdf_get_man
     - `PDFGetManInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.PDFGetManInterface>`_
   * - pdf_prep
     - `PDFPrepInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.PDFPrepInterface>`_
   * - pdf_prep_man
     - `PDFPrepManInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.PDFPrepManInterface>`_
   * - screen
     - `ScreenInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.ScreenInterface>`_
   * - data
     - `DataInterface <packages/package_interfaces.html#colrev.package_manager.interfaces.DataInterface>`_

* Set ``ci_supported`` flag to True/False depending on, if this package is not able to run in CI environment

Documentation
-----------------

* Link the documentation (`README.md`) in the pyproject.toml.
* To integrate the package documentation into the official CoLRev documentation, run the ``colrev env --update_package_list`` command. This updates the `package_endpoints.json <https://github.com/CoLRev-Environment/colrev/blob/main/docs/source/package_endpoints.json>`_, and the `search_source_types.json <https://github.com/CoLRev-Environment/colrev/blob/main/colrev/docs/source/search_source_types.json>`_, which are used to generate the documentation pages.
* See `tests/REAMDE.md <https://github.com/CoLRev-Environment/colrev/tree/main/docs>` for details on building the CoLRev docs.

Testing
-----------

* Tests for built-in packages are currently in the tests of the CoLRev packages.
* See `tests/REAMDE.md <https://github.com/CoLRev-Environment/colrev/tree/main/tests>` for details.

Publication
------------

* Currently, built-in packages are not published separately. They are automatically provided with every PyPI-release of CoLRev.

Best practices
------------------

* Remember to install CoLRev in editable mode, so that changes are immediately available (run `pip install -e /path/to/cloned/colrev`)
* Check the other package implementations for getting a good idea on how to proceed
* Use the `colrev constants <https://github.com/CoLRev-Environment/colrev/blob/main/colrev/constants.py>`__
* Get paths from review_manager
* Use the ``logger`` and ``colrev_report_logger`` to help users examine and validate the process, including links to the docs where instructions for tracing and fixing errors are available.
* Before committing do a pre-commit test
* Use poetry for dependency management (run `poetry add <package_name>` to add a new dependency)
* Once the package development is completed, make a PR to the CoLRev, with brief description of the package.

Package development resources
------------------------------

.. toctree::
   :maxdepth: 1

   packages/package_interfaces
   packages/linters
   packages/custom_packages
   packages/python
   packages/r
