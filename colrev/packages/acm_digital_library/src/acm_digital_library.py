#! /usr/bin/env python
"""SearchSource: ACM Digital Library"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import zope.interface
from dacite import from_dict
from dataclasses_jsonschema import JsonSchemaMixin

import colrev.package_manager.interfaces
import colrev.package_manager.package_manager
import colrev.package_manager.package_settings
import colrev.record.record
from colrev.constants import Fields
from colrev.constants import SearchSourceHeuristicStatus
from colrev.constants import SearchType

# pylint: disable=unused-argument
# pylint: disable=duplicate-code


@zope.interface.implementer(colrev.package_manager.interfaces.SearchSourceInterface)
@dataclass
class ACMDigitalLibrarySearchSource(JsonSchemaMixin):
    """ACM digital Library"""

    settings_class = colrev.package_manager.package_settings.DefaultSourceSettings
    endpoint = "colrev.acm_digital_library"
    # Note : the ID contains the doi
    # "https://dl.acm.org/doi/{{ID}}"
    source_identifier = "doi"
    search_types = [SearchType.DB]

    ci_supported: bool = False
    heuristic_status = SearchSourceHeuristicStatus.supported
    short_name = "ACM Digital Library"
    docs_link = (
        "https://github.com/CoLRev-Environment/colrev/blob/main/colrev/"
        + "packages/search_sources/acm_digital_library.md"
    )
    db_url = "https://dl.acm.org/"

    def __init__(
        self, *, source_operation: colrev.process.operation.Operation, settings: dict
    ) -> None:
        self.search_source = from_dict(data_class=self.settings_class, data=settings)
        self.review_manager = source_operation.review_manager
        self.operation = source_operation

    @classmethod
    def heuristic(cls, filename: Path, data: str) -> dict:
        """Source heuristic for ACM dDigital Library"""

        result = {"confidence": 0.0}
        # Simple heuristic:
        if "publisher = {Association for Computing Machinery}," in data:
            result["confidence"] = 0.7
            return result
        # We may also check whether the ID=doi=url
        return result

    @classmethod
    def add_endpoint(
        cls,
        operation: colrev.ops.search.Search,
        params: dict,
    ) -> colrev.settings.SearchSource:
        """Add SearchSource as an endpoint (based on query provided to colrev search -a )"""

        search_type = operation.select_search_type(
            search_types=cls.search_types, params=params
        )

        if search_type == SearchType.DB:
            return operation.add_db_source(
                search_source_cls=cls,
                params=params,
            )

        raise NotImplementedError

    def search(self, rerun: bool) -> None:
        """Run a search of ACM Digital Library"""

        if self.search_source.search_type == SearchType.DB:
            if self.search_source.filename.suffix in [".bib"]:
                self.operation.run_db_search(  # type: ignore
                    search_source_cls=self.__class__,
                    source=self.search_source,
                )
                return

            raise NotImplementedError
        raise NotImplementedError

    def prep_link_md(
        self,
        prep_operation: colrev.ops.prep.Prep,
        record: colrev.record.record.Record,
        save_feed: bool = True,
        timeout: int = 10,
    ) -> colrev.record.record.Record:
        """Not implemented"""
        return record

    def load(self, load_operation: colrev.ops.load.Load) -> dict:
        """Load the records from the SearchSource file"""

        if self.search_source.filename.suffix == ".bib":

            def field_mapper(record_dict: dict) -> None:
                record_dict.pop("url", None)
                record_dict.pop("publisher", None)
                record_dict.pop("numpages", None)
                record_dict.pop("month", None)

                if "issue_date" in record_dict:
                    record_dict[f"{self.endpoint}.issue_date"] = record_dict.pop(
                        "issue_date"
                    )
                if "location" in record_dict:
                    record_dict[Fields.ADDRESS] = record_dict.pop("location", None)
                if "articleno" in record_dict:
                    record_dict[f"{self.endpoint}.articleno"] = record_dict.pop(
                        "articleno"
                    )

            records = colrev.loader.load_utils.load(
                filename=self.search_source.filename,
                unique_id_field="ID",
                field_mapper=field_mapper,
                logger=self.review_manager.logger,
            )

            return records

        raise NotImplementedError

    # pylint: disable=colrev-missed-constant-usage
    def prepare(
        self, record: colrev.record.record.Record, source: colrev.settings.SearchSource
    ) -> colrev.record.record.Record:
        """Source-specific preparation for ACM Digital Library"""

        return record
