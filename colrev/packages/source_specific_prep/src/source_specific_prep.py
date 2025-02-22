#! /usr/bin/env python
"""Source-specific preparation as a prep operation"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import zope.interface
from dataclasses_jsonschema import JsonSchemaMixin

import colrev.package_manager.interfaces
import colrev.package_manager.package_manager
import colrev.package_manager.package_settings
import colrev.record.record
from colrev.constants import EndpointType
from colrev.constants import Fields

# pylint: disable=duplicate-code


# pylint: disable=too-few-public-methods


@zope.interface.implementer(colrev.package_manager.interfaces.PrepInterface)
@dataclass
class SourceSpecificPrep(JsonSchemaMixin):
    """Prepares records based on the prepare scripts specified by the SearchSource"""

    source_correction_hint = "check with the developer"
    ci_supported: bool = True

    always_apply_changes = True
    settings_class = colrev.package_manager.package_settings.DefaultSettings

    def __init__(
        self,
        *,
        prep_operation: colrev.ops.prep.Prep,
        settings: dict,
    ) -> None:
        self.settings = self.settings_class.load_settings(data=settings)
        self.review_manager = prep_operation.review_manager

        self.package_manager = prep_operation.review_manager.get_package_manager()

    def prepare(
        self, record: colrev.record.record_prep.PrepRecord
    ) -> colrev.record.record.Record:
        """Prepare the record by applying source-specific fixes"""

        # Note : we take the first origin (ie., the source-specific prep should
        # be one of the first in the prep-list)
        origin_source = record.data[Fields.ORIGIN][0].split("/")[0]

        sources = [
            s
            for s in self.review_manager.settings.sources
            if s.filename == Path("data/search") / Path(origin_source)
        ]

        for source in sources:
            # if source.endpoint not in self.search_sources.packages:
            #     continue
            # endpoint = self.search_sources.packages[source.endpoint]
            search_source_class = self.package_manager.get_package_endpoint_class(
                package_type=EndpointType.search_source,
                package_identifier=source.endpoint,
            )
            endpoint = search_source_class(
                source_operation=self, settings=source.get_dict()
            )

            if callable(endpoint.prepare):
                record = endpoint.prepare(record, source)
            else:
                print(f"error: {source.endpoint}")

        if "howpublished" in record.data and Fields.URL not in record.data:
            if Fields.URL in record.data["howpublished"]:
                record.rename_field(key="howpublished", new_key=Fields.URL)
                record.update_field(
                    key=Fields.URL,
                    value=record.data[Fields.URL].replace("\\url{", "").rstrip("}"),
                    source="source_specific_prep",
                )

        if "webpage" == record.data[Fields.ENTRYTYPE].lower() or (
            "misc" == record.data[Fields.ENTRYTYPE].lower()
            and Fields.URL in record.data
        ):
            record.update_field(
                key=Fields.ENTRYTYPE, value="online", source="source_specific_prep"
            )

        return record
