colrev screen
---------------------------------------------

.. |EXPERIMENTAL| image:: https://img.shields.io/badge/status-experimental-blue
   :height: 12pt
   :target: https://colrev.readthedocs.io/en/latest/dev_docs/dev_status.html
.. |MATURING| image:: https://img.shields.io/badge/status-maturing-yellowgreen
   :height: 12pt
   :target: https://colrev.readthedocs.io/en/latest/dev_docs/dev_status.html
.. |STABLE| image:: https://img.shields.io/badge/status-stable-brightgreen
   :height: 12pt
   :target: https://colrev.readthedocs.io/en/latest/dev_docs/dev_status.html

In the ``colrev screen`` operation, records transition from ``pdf_prepared`` to ``rev_included`` or ``rev_excluded``. Decisions on individual screening criteria (if any) are reported in the ``screening_criteria`` field.


The selection of screening criteria is recorded when initializing the screen.

.. code:: bash

	colrev screen [options]

    # Include all papers
    colrev screen --include_all

    # Splits the screen between n researchers. Simply share the output with the researchers and ask them to run the commands in their local CoLRev project.
    colrev screen --create_split INT

    # Complete the screen for the specified split.
    colrev screen --split STR


The following options for ``screen`` are available:

.. datatemplate:json:: ../../package_endpoints.json

    {{ make_list_table_from_mappings(
        [("Identifier", "package_endpoint_identifier"), ("Screen packages", "short_description"), ("Status", "status")],
        data['screen'],
        title='',
        columns=[25,55,20]
        ) }}
