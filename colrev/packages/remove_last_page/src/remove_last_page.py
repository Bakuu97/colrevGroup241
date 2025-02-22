#! /usr/bin/env python
"""Last-page removal as a PDF preparation operation"""
from __future__ import annotations

import shutil
import typing
from dataclasses import dataclass
from pathlib import Path

import zope.interface
from dataclasses_jsonschema import JsonSchemaMixin
from PyPDF2 import PdfFileReader

import colrev.package_manager.interfaces
import colrev.package_manager.package_manager
import colrev.package_manager.package_settings
from colrev.constants import Fields
from colrev.constants import Filepaths

# pylint: disable=duplicate-code


# pylint: disable=too-few-public-methods


@zope.interface.implementer(colrev.package_manager.interfaces.PDFPrepInterface)
@dataclass
class PDFLastPage(JsonSchemaMixin):
    """Prepare PDFs by removing unnecessary last pages (e.g. copyright notices, cited-by infos)"""

    settings_class = colrev.package_manager.package_settings.DefaultSettings
    ci_supported: bool = False

    def __init__(
        self,
        *,
        pdf_prep_operation: colrev.ops.pdf_prep.PDFPrep,  # pylint: disable=unused-argument
        settings: dict,
    ) -> None:
        self.settings = self.settings_class.load_settings(data=settings)
        self.review_manager = pdf_prep_operation.review_manager

    def prep_pdf(
        self,
        record: colrev.record.record_pdf.PDFRecord,
        pad: int,  # pylint: disable=unused-argument
    ) -> dict:
        """Prepare the PDF by removing additional materials (if any)"""

        if not record.data[Fields.FILE].endswith(".pdf"):
            return record.data

        lp_path = Filepaths.LOCAL_ENVIRONMENT_DIR / Path(".lastpages")
        lp_path.mkdir(exist_ok=True)

        def _get_last_pages(*, pdf: str) -> typing.List[int]:
            last_pages: typing.List[int] = []
            try:
                pdf_reader = PdfFileReader(str(pdf), strict=False)
            except ValueError:
                return last_pages

            last_page_nr = len(pdf_reader.pages) - 1

            last_page_average_hash_16 = record.get_pdf_hash(
                page_nr=last_page_nr + 1, hash_size=16
            )

            if last_page_nr == 1:
                return last_pages

            # Note : to generate hashes from a directory containing single-page PDFs:
            # colrev pdf-prep --pdf_hash path
            last_page_hashes = [
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffff83ff83ff",
                "ffff80038007ffffffffffffffffffffffffffffffffffffffffffffffffffff",
                "c3fbc003c003ffc3ff83ffc3ffffffffffffffffffffffffffffffffffffffff",
                "ffff80038007ffffffffffffffffffffffffffffffffffffffffffffffffffff",
                "ffff80038001ffff7fff7fff7fff7fff7fff7fff7fff7fffffffffffffffffff",
                "ffff80008003ffffffffffffffffffffffffffffffffffffffffffffffffffff",
                "ffff80038007ffffffffffffffffffffffffffffffffffffffffffffffffffff",
                "ffff80018001ffffffffffffffffffffffffffffffffffffffffffffffffffff",
            ]

            if str(last_page_average_hash_16) in last_page_hashes:
                last_pages.append(last_page_nr)

            res = pdf_reader.getPage(last_page_nr).extract_text()
            last_page_text = res.replace(" ", "").replace("\n", "").lower()

            # ME Sharpe last page
            if (
                "propertyofm.e.sharpeinc.anditscontentmayno"
                + "tbecopiedoremailedtomultiplesi"
                + "tesorpostedtoalistservwithoutthecopyrightholder"
                in last_page_text
            ):
                last_pages.append(last_page_nr)

            # CAIS last page / editorial board
            if all(
                x in last_page_text
                for x in [
                    "caisadvisoryboard",
                    "caiseditorialboard",
                    "caissenioreditors",
                ]
            ):
                last_pages.append(last_page_nr)

            return list(set(last_pages))

        last_pages = _get_last_pages(pdf=record.data[Fields.FILE])
        if not last_pages:
            return record.data
        if last_pages:
            original = self.review_manager.path / Path(record.data[Fields.FILE])
            file_copy = self.review_manager.path / Path(
                record.data[Fields.FILE].replace(".pdf", "_wo_lp.pdf")
            )
            shutil.copy(original, file_copy)

            record.extract_pages(
                pages=last_pages,
                project_path=self.review_manager.path,
                save_to_path=lp_path,
            )
            self.review_manager.report_logger.info(
                f"removed last page for ({record.data[Fields.ID]})"
            )
        return record.data
