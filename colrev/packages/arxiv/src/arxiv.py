#! /usr/bin/env python
"""SearchSource: arXiv"""
from __future__ import annotations

import typing
from dataclasses import dataclass
from multiprocessing import Lock
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests
import zope.interface
from dacite import from_dict

import colrev.exceptions as colrev_exceptions
import colrev.package_manager.interfaces
import colrev.package_manager.package_manager
import colrev.package_manager.package_settings
import colrev.record.record
import colrev.record.record_prep
from colrev.constants import Fields
from colrev.constants import SearchSourceHeuristicStatus
from colrev.constants import SearchType

# pylint: disable=unused-argument
# pylint: disable=duplicate-code


@zope.interface.implementer(colrev.package_manager.interfaces.SearchSourceInterface)
@dataclass
class ArXivSource:
    """SearchSource for arXiv"""

    settings_class = colrev.package_manager.package_settings.DefaultSourceSettings
    endpoint = "colrev.arxiv"
    source_identifier = "arxivid"
    search_types = [SearchType.API]
    api_search_supported = True
    ci_supported: bool = True
    heuristic_status = SearchSourceHeuristicStatus.supported
    short_name = "arXiv"
    docs_link = (
        "https://github.com/CoLRev-Environment/colrev/blob/main/"
        + "colrev/packages/search_sources/arxiv.md"
    )
    db_url = "https://arxiv.org/"
    _arxiv_md_filename = Path("data/search/md_arxiv.bib")

    def __init__(
        self,
        *,
        source_operation: colrev.process.operation.Operation,
        settings: typing.Optional[dict] = None,
    ) -> None:
        self.review_manager = source_operation.review_manager
        if settings:
            # arXiv as a search_source
            self.search_source = from_dict(
                data_class=self.settings_class, data=settings
            )
        else:
            # arXiv as an md-prep source
            arxiv_md_source_l = [
                s
                for s in self.review_manager.settings.sources
                if s.filename == self._arxiv_md_filename
            ]
            if arxiv_md_source_l:
                self.search_source = arxiv_md_source_l[0]
            else:
                self.search_source = colrev.settings.SearchSource(
                    endpoint="colrev.arxiv",
                    filename=self._arxiv_md_filename,
                    search_type=SearchType.API,
                    search_parameters={},
                    comment="",
                )

            self.arxiv_lock = Lock()

        self.operation = source_operation
        self.quality_model = self.review_manager.get_qm()
        _, self.email = self.review_manager.get_committer()

    @classmethod
    def heuristic(cls, filename: Path, data: str) -> dict:
        """Source heuristic for ArXiv"""

        result = {"confidence": 0.0}

        return result

    @classmethod
    def add_endpoint(
        cls,
        operation: colrev.ops.search.Search,
        params: dict,
    ) -> colrev.settings.SearchSource:
        """Add SearchSource as an endpoint (based on query provided to colrev search -a )"""

        if len(params) == 0:
            add_source = operation.add_api_source(endpoint=cls.endpoint)
            return add_source

        # pylint: disable=colrev-missed-constant-usage
        if "url" in params:
            host = urlparse(params["url"]).hostname

            if host and host.endswith("arxiv.org"):
                query = params["url"].replace("https://arxiv.org/search/?query=", "")
                query = query[: query.find("&searchtype")]

                filename = operation.get_unique_filename(file_path_string="arxiv")

                add_source = colrev.settings.SearchSource(
                    endpoint="colrev.arxiv",
                    filename=filename,
                    search_type=SearchType.API,
                    search_parameters={"query": query},
                    comment="",
                )
                return add_source

        raise NotImplementedError

    def validate_source(
        self,
        search_operation: colrev.ops.search.Search,
        source: colrev.settings.SearchSource,
    ) -> None:
        """Validate the SearchSource (parameters etc.)"""

        search_operation.review_manager.logger.debug(
            f"Validate SearchSource {source.filename}"
        )

        if source.filename.name != self._arxiv_md_filename.name:
            if "query" not in source.search_parameters:
                raise colrev_exceptions.InvalidQueryException(
                    f"Source missing query search_parameter ({source.filename})"
                )

            # if "query_file" in source.search_parameters:
            # ...

        search_operation.review_manager.logger.debug(
            f"SearchSource {source.filename} validated"
        )

    def check_availability(
        self, *, source_operation: colrev.process.operation.Operation
    ) -> None:
        """Check status (availability) of the ArXiv API"""

        # try:
        #     # pylint: disable=duplicate-code
        #     test_rec = {
        #         "author": "Wang, R E and Demszky, D ",
        #         "title": "Is ChatGPT a Good Teacher Coach?"
        #         "Measuring Zero-Shot Performance For Scoring and Providing "
        #           + \ "Actionable Insights on Classroom Instruction ",
        #         "ENTRYTYPE": "article",  # might not be needed in ArXiv
        #         "arxivid": "arXiv:2306.03090",
        #     }
        #     returned_record_dict = self._arxiv_query_id(
        #         arxiv_id=test_rec["arxivid"],
        #         timeout=20,
        #     )

        #     if returned_record_dict:
        #         assert returned_record_dict["title"] == test_rec["title"]
        #         assert returned_record_dict["author"] == test_rec["author"]
        #     else:
        #         if not source_operation.force_mode:
        #             raise colrev_exceptions.ServiceNotAvailableException("ArXiv")
        # except (requests.exceptions.RequestException, IndexError) as exc:
        #     print(exc)
        #     if not source_operation.force_mode:
        #         raise colrev_exceptions.ServiceNotAvailableException("ArXiv") from exc

    # def _arxiv_query_id(
    #     self,
    #     *,
    #     arxiv_id: str,
    #     timeout: int = 60,
    # ) -> dict:
    #     """Retrieve records from ArXiv based on a query"""

    #     # Query using ID List prefix ?? - wo hast du das gefunden?
    #     try:
    #         prefix = "id_list"
    #         url = (
    #             "https://export.arxiv.org/api/query?search_query="
    #             + f"list={prefix}:&id={arxiv_id}"
    #         )

    #         headers = {"user-agent": f"{__name__} (mailto:{self.email})"}
    #         session = self.review_manager.get_cached_session()

    #         # review_manager.logger.debug(url)
    #         ret = session.request("GET", url, headers=headers, timeout=timeout)
    #         ret.raise_for_status()
    #         if ret.status_code != 200:
    #             # review_manager.logger.debug(
    #             #     f"crossref_query failed with status {ret.status_code}"
    #             # )
    #             return {"arxiv_id": arxiv_id}

    #         input(str.encode(ret.text))
    #         root = fromstring(str.encode(ret.text))
    #         retrieved_record = self._arxiv_xml_to_record(root=root)
    #         if not retrieved_record:
    #             return {"arxiv_id": arxiv_id}
    #     except requests.exceptions.RequestException:
    #         return {"arxiv_id": arxiv_id}
    #     # pylint: disable=duplicate-code
    #     except OperationalError as exc:
    #         raise colrev_exceptions.ServiceNotAvailableException(
    #             "sqlite, required for requests CachedSession "
    #             "(possibly caused by concurrent operations)"
    #         ) from exc

    #     return retrieved_record

    def prep_link_md(
        self,
        prep_operation: colrev.ops.prep.Prep,
        record: colrev.record.record.Record,
        save_feed: bool = True,
        timeout: int = 10,
    ) -> colrev.record.record.Record:
        """Retrieve masterdata fromArXiv based on similarity with the record provided"""
        # https://info.arxiv.org/help/api/user-manual.html#_query_interface
        # id_list
        return record

    # pylint: disable=too-many-branches
    # pylint: disable=colrev-missed-constant-usage
    def _parse_record(self, entry: dict) -> dict:
        entry[Fields.ENTRYTYPE] = "techreport"
        entry["arxivid"] = entry.pop("id").replace("http://arxiv.org/abs/", "")
        entry[Fields.AUTHOR] = " and ".join([a["name"] for a in entry.pop("authors")])
        entry[Fields.YEAR] = entry.pop("published")[:4]
        entry[Fields.ABSTRACT] = entry.pop("summary")
        entry[Fields.ABSTRACT] = (
            entry[Fields.ABSTRACT].replace("\n", " ").replace("\r", " ")
        )
        if "arxiv_journal_ref" in entry:
            entry["arxiv_journal_ref"] = (
                entry["arxiv_journal_ref"].replace("\n", " ").replace("\r", " ")
            )
        entry[Fields.TITLE] = entry["title"].replace("\n ", "")
        if "arxiv_doi" in entry:
            entry[Fields.DOI] = entry.pop("arxiv_doi")
        if "links" in entry:
            for link in entry["links"]:
                if link["type"] == "application/pdf":
                    entry[Fields.FULLTEXT] = link["href"]
                else:
                    entry[Fields.URL] = link["href"]
        if "link" in entry:
            if "url" in entry:
                del entry["link"]
            else:
                entry[Fields.URL] = entry.pop("link")
        if "arxiv_comment" in entry:
            entry[Fields.KEYWORDS] = (
                entry.pop("arxiv_comment").replace("Key words: ", "").replace("\n", "")
            )

        fields_to_remove = [
            "links",
            "href",
            "guidislink",
            "summary_detail",
            "title_detail",
            "updated",
            "updated_parsed",
            "author_detail",
            "published_parsed",
            "arxiv_primary_category",
            "tags",
        ]
        for field_to_remove in fields_to_remove:
            if field_to_remove in entry:
                del entry[field_to_remove]

        if "keywords" in entry and "pages" in entry["keywords"]:
            del entry["keywords"]
        return entry

    def _get_arxiv_ids(self, query: str, retstart: int) -> typing.List[dict]:
        url = (
            "https://export.arxiv.org/api/query?search_query="
            + f"all:{query}&start={retstart}&max_results=20"
        )
        feed = feedparser.parse(url)
        return feed["entries"]

    def _get_arxiv_query_return(self) -> typing.Iterator[dict]:
        params = self.search_source.search_parameters
        retstart = 0
        while True:
            entries = self._get_arxiv_ids(query=params["query"], retstart=retstart)
            if not entries:
                break
            for entry in entries:
                yield self._parse_record(entry)

            retstart += 20

    def _run_parameter_search(
        self,
        *,
        arxiv_feed: colrev.ops.search_api_feed.SearchAPIFeed,
        rerun: bool,
    ) -> None:
        if rerun:
            self.review_manager.logger.info(
                "Performing a search of the full history (may take time)"
            )

        try:
            for record_dict in self._get_arxiv_query_return():
                try:
                    # Note : discard "empty" records
                    if "" == record_dict.get(
                        Fields.AUTHOR, ""
                    ) and "" == record_dict.get(Fields.TITLE, ""):
                        self.review_manager.logger.warning(
                            f"Skipped record: {record_dict}"
                        )
                        continue

                    prep_record = colrev.record.record_prep.PrepRecord(record_dict)

                    added = arxiv_feed.add_update_record(prep_record)

                    # Note : only retrieve/update the latest deposits (unless in rerun mode)
                    if not added and not rerun:
                        # problem: some publishers don't necessarily
                        # deposit papers chronologically
                        break
                except colrev_exceptions.NotFeedIdentifiableException:
                    continue

            arxiv_feed.save()

        except requests.exceptions.JSONDecodeError as exc:
            # watch github issue:
            # https://github.com/fabiobatalha/crossrefapi/issues/46
            if "504 Gateway Time-out" in str(exc):
                raise colrev_exceptions.ServiceNotAvailableException(
                    "Crossref (check https://status.crossref.org/)"
                )
            raise colrev_exceptions.ServiceNotAvailableException(
                f"Crossref (check https://status.crossref.org/) ({exc})"
            )

    # def _run_md_search_update(
    #     self,
    #     *,
    #     arxiv_feed: colrev.ops.search.SearchAPIFeed,
    # ) -> None:
    #     records = self.review_manager.dataset.load_records_dict()

    #     for feed_record_dict in arxiv_feed.feed_records.values():
    #         feed_record = colrev.record.record.Record(feed_record_dict)

    #         try:
    #             retrieved_record = self._arxiv_query_id(
    #                 arxiv_id=feed_record_dict["arxivid"]
    #             )

    #             if retrieved_record["arxivid"] != feed_record.data["arxivid"]:
    #                 continue

    # prev_record_dict_version = (
    #     dblp_feed.get_prev_feed_record(
    #         retrieved_record=feed_record
    #     )
    # )
    #         retrieved_record = colrev.record.record.Record(retrieved_record)
    #         arxiv_feed.add_update_record(retrieved_record)

    #         changed = self.operation.update_existing_record(
    #             records=records,
    #             record_dict=retrieved_record,
    #             prev_record_dict_version=prev_record_dict_version,
    #             source=self.search_source,
    #         )
    #         if changed:
    #             arxiv_feed.nr_changed += 1
    #         except (
    #             colrev_exceptions.RecordNotFoundInPrepSourceException,
    #             colrev_exceptions.NotFeedIdentifiableException,
    #         ):
    #             continue

    #     arxiv_feed.save()

    def search(self, rerun: bool) -> None:
        """Run a search of ArXiv"""

        arxiv_feed = self.search_source.get_api_feed(
            review_manager=self.review_manager,
            source_identifier=self.source_identifier,
            update_only=(not rerun),
        )

        # if self.search_source.search_type == SearchType.MD:
        #     self._run_md_search_update(
        #         arxiv_feed=arxiv_feed,
        #     )

        if self.search_source.search_type == SearchType.API:
            self._run_parameter_search(
                arxiv_feed=arxiv_feed,
                rerun=rerun,
            )

    def load(self, load_operation: colrev.ops.load.Load) -> dict:
        """Load the records from the SearchSource file"""

        # for API-based searches
        if self.search_source.filename.suffix == ".bib":
            records = colrev.loader.load_utils.load(
                filename=self.search_source.filename,
                logger=self.review_manager.logger,
            )
            for record in records.values():
                record["institution"] = "ArXiv"
            return records

        raise NotImplementedError

    def load_fixes(
        self,
        load_operation: colrev.ops.load.Load,
        source: colrev.settings.SearchSource,
        records: typing.Dict,
    ) -> dict:
        """Load fixes for ArXiv"""
        return records

    def prepare(
        self, record: colrev.record.record.Record, source: colrev.settings.SearchSource
    ) -> colrev.record.record.Record:
        """Source-specific preparation for ArXiv"""

        if Fields.AUTHOR in record.data:
            record.data[Fields.AUTHOR] = (
                colrev.record.record_prep.PrepRecord.format_author_field(
                    record.data[Fields.AUTHOR]
                )
            )

        return record
