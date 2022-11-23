#!/usr/bin/env python3
"""The CoLRev review manager (main entrypoint)."""
from __future__ import annotations

import logging
import os
import pprint
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path

import requests_cache
import yaml

import colrev.checker
import colrev.dataset
import colrev.env.utils
import colrev.exceptions as colrev_exceptions
import colrev.logger
import colrev.operation
import colrev.record
import colrev.settings

PASS, FAIL = 0, 1


class ReviewManager:
    """Class for managing individual CoLRev review project (repositories)"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
    # pylint: disable=import-outside-toplevel
    # pylint: disable=redefined-outer-name

    notified_next_operation = None
    """ReviewManager was notified for the upcoming process and
    will provide access to the Dataset"""

    SETTINGS_RELATIVE = Path("settings.json")
    REPORT_RELATIVE = Path(".report.log")
    CORRECTIONS_PATH_RELATIVE = Path(".corrections")
    PDF_DIR_RELATIVE = Path("data/pdfs")
    SEARCHDIR_RELATIVE = Path("data/search")
    README_RELATIVE = Path("readme.md")
    STATUS_RELATIVE = Path("status.yaml")
    OUTPUT_DIR_RELATIVE = Path("output")
    DATA_DIR_RELATIVE = Path("data")

    dataset: colrev.dataset.Dataset
    """The review dataset object"""

    path: Path
    """Path of the project repository"""

    def __init__(
        self,
        *,
        path_str: str = None,
        force_mode: bool = False,
        verbose_mode: bool = False,
        navigate_to_home_dir: bool = True,
    ) -> None:

        self.force_mode = force_mode
        """Force mode variable (bool)"""
        self.verbose_mode = verbose_mode
        """Verbose mode variable (bool)"""

        if navigate_to_home_dir:
            self.path = self.__get_project_home_dir(path_str=path_str)
        else:
            self.path = Path.cwd()

        self.settings_path = self.path / self.SETTINGS_RELATIVE
        self.report_path = self.path / self.REPORT_RELATIVE
        self.corrections_path = self.path / self.CORRECTIONS_PATH_RELATIVE
        self.pdf_dir = self.path / self.PDF_DIR_RELATIVE
        self.search_dir = self.path / self.SEARCHDIR_RELATIVE
        self.readme = self.path / self.README_RELATIVE
        self.status = self.path / self.STATUS_RELATIVE
        self.output_dir = self.path / self.OUTPUT_DIR_RELATIVE
        self.data_dir = self.path / self.DATA_DIR_RELATIVE

        try:
            if self.settings_path.is_file():
                self.data_dir.mkdir(exist_ok=True)
                self.search_dir.mkdir(exist_ok=True)
                self.pdf_dir.mkdir(exist_ok=True)
                self.output_dir.mkdir(exist_ok=True)

            # Start LocalIndex to prevent waiting times
            self.get_local_index(startup_without_waiting=True)

            if self.verbose_mode:
                self.report_logger = colrev.logger.setup_report_logger(
                    review_manager=self, level=logging.DEBUG
                )
                """Logger for the commit report"""
                self.logger = colrev.logger.setup_logger(
                    review_manager=self, level=logging.DEBUG
                )
                """Logger for processing information"""
            else:
                self.report_logger = colrev.logger.setup_report_logger(
                    review_manager=self, level=logging.INFO
                )
                self.logger = colrev.logger.setup_logger(
                    review_manager=self, level=logging.INFO
                )

            self.environment_manager = self.get_environment_manager()
            (
                self.committer,
                self.email,
            ) = self.environment_manager.get_name_mail_from_git()

            self.p_printer = pprint.PrettyPrinter(indent=4, width=140, compact=False)
            self.settings = self.load_settings()
            self.dataset = colrev.dataset.Dataset(review_manager=self)

        except Exception as exc:  # pylint: disable=broad-except
            if force_mode:
                if verbose_mode:
                    self.logger.debug(exc)
            else:
                raise exc

    def __get_project_home_dir(self, *, path_str: str = None) -> Path:
        if path_str:
            return Path(path_str)

        original_dir = Path.cwd()
        while ".git" not in [f.name for f in Path.cwd().iterdir() if f.is_dir()]:
            os.chdir("..")
            if Path("/") == Path.cwd():
                os.chdir(original_dir)
                break
        return Path.cwd()

    def load_settings(self) -> colrev.settings.Settings:
        """Load the settings"""
        return colrev.settings.load_settings(review_manager=self)

    def save_settings(self) -> None:
        """Save the settings"""
        colrev.settings.save_settings(review_manager=self)

    def reset_report_logger(self) -> None:
        """Reset the report logger"""
        colrev.logger.reset_report_logger(review_manager=self)

    def check_repo(self) -> dict:
        """Check the repository"""
        checker = colrev.checker.Checker(review_manager=self)
        return checker.check_repo()

    def in_virtualenv(self) -> bool:
        """Check whether CoLRev operates in a virtual environment"""
        checker = colrev.checker.Checker(review_manager=self)
        return checker.in_virtualenv()

    def check_repository_setup(self) -> None:
        """Check the repository setup"""
        checker = colrev.checker.Checker(review_manager=self)
        checker.check_repository_setup()

    def get_colrev_versions(self) -> list[str]:
        """Get the CoLRev versions"""
        checker = colrev.checker.Checker(review_manager=self)
        return checker.get_colrev_versions()

    def report(self, *, msg_file: Path) -> dict:
        """Append commit-message report if not already available
        Entrypoint for pre-commit hooks)
        """
        import colrev.ops.commit
        import colrev.ops.correct

        with open(msg_file, encoding="utf8") as file:
            available_contents = file.read()

        with open(msg_file, "w", encoding="utf8") as file:
            file.write(available_contents)
            # Don't append if it's already there
            update = False
            if "Command" not in available_contents:
                update = True
            if "Properties" in available_contents:
                update = False
            if update:
                commit = colrev.ops.commit.Commit(
                    review_manager=self,
                    msg=available_contents,
                    manual_author=True,
                    script_name="MANUAL",
                )
                commit.update_report(msg_file=msg_file)

        colrev.operation.CheckOperation(review_manager=self)  # to notify
        corrections_operation = colrev.ops.correct.Corrections(review_manager=self)
        corrections_operation.check_corrections_of_curated_records()

        return {"msg": "TODO", "status": 0}

    def sharing(self) -> dict:
        """Check whether sharing requirements are met
        Entrypoint for pre-commit hooks)
        """

        self.notified_next_operation = colrev.operation.OperationsType.check
        advisor = self.get_advisor()
        sharing_advice = advisor.get_sharing_instructions()
        return sharing_advice

    def format_records_file(self) -> dict:
        """Format the records file Entrypoint for pre-commit hooks)"""

        if not self.dataset.records_file.is_file():
            return {"status": PASS, "msg": "Everything ok."}

        try:
            colrev.operation.FormatOperation(review_manager=self)  # to notify
            changed = self.dataset.format_records_file()
            self.update_status_yaml()
            self.settings = self.load_settings()
            self.save_settings()
        except (
            colrev_exceptions.UnstagedGitChangesError,
            colrev_exceptions.StatusFieldValueError,
        ) as exc:
            return {"status": FAIL, "msg": f"{type(exc).__name__}: {exc}"}

        if changed:
            return {"status": FAIL, "msg": "records file formatted"}

        return {"status": PASS, "msg": "Everything ok."}

    def notify(
        self, *, operation: colrev.operation.Operation, state_transition: bool = True
    ) -> None:
        """Notify the review_manager about the next operation"""

        try:
            if state_transition:
                operation.check_precondition()
            self.notified_next_operation = operation.type
            self.dataset.reset_log_if_no_changes()
        except AttributeError as exc:
            if self.force_mode:
                pass
            else:
                raise exc

    def update_status_yaml(self, *, add_to_git: bool = True) -> None:
        """Update the status.yaml"""

        status_stats = self.get_status_stats()
        exported_dict = asdict(status_stats)
        with open(self.status, "w", encoding="utf8") as file:
            yaml.dump(exported_dict, file, allow_unicode=True)
        if add_to_git:
            self.dataset.add_changes(path=self.STATUS_RELATIVE)

    def create_commit(
        self,
        *,
        msg: str,
        manual_author: bool = False,
        script_call: str = "",
        saved_args: dict = None,
        realtime_override: bool = False,
    ) -> bool:
        """Create a commit (including a commit report)"""
        import colrev.ops.commit

        commit = colrev.ops.commit.Commit(
            review_manager=self,
            msg=msg,
            manual_author=manual_author,
            script_name=script_call,
            saved_args=saved_args,
            realtime_override=realtime_override,
        )
        ret = commit.create()
        return ret

    def get_upgrade(self) -> colrev.ops.upgrade.Upgrade:
        """Get an upgrade object"""

        import colrev.ops.upgrade

        return colrev.ops.upgrade.Upgrade(review_manager=self)

    def get_repair(self) -> colrev.ops.repair.Repair:
        """Get a a repair object"""

        import colrev.ops.repair

        return colrev.ops.repair.Repair(review_manager=self)

    def get_remove_operation(self) -> colrev.ops.remove.Remove:
        """Get a a remove object"""

        import colrev.ops.remove

        return colrev.ops.remove.Remove(review_manager=self)

    def get_merge_operation(self) -> colrev.ops.merge.Merge:
        """Get a merge object"""

        import colrev.ops.merge

        return colrev.ops.merge.Merge(review_manager=self)

    def get_compare_operation(self) -> colrev.ops.compare.Compare:
        """Get a a compare object"""

        import colrev.ops.compare

        return colrev.ops.compare.Compare(review_manager=self)

    def get_advisor(self) -> colrev.advisor.Advisor:
        """Get an advisor object"""

        import colrev.advisor

        return colrev.advisor.Advisor(review_manager=self)

    def get_checker(self) -> colrev.checker.Checker:
        """Get a checker object"""

        return colrev.checker.Checker(review_manager=self)

    def get_status_stats(self) -> colrev.ops.status.StatusStats:
        """Get a status stats object"""

        import colrev.ops.status

        return colrev.ops.status.StatusStats(review_manager=self)

    def get_completeness_condition(self) -> bool:
        """Get the completeness condition"""
        status_stats = self.get_status_stats()
        return status_stats.completeness_condition

    @classmethod
    def get_local_index(
        cls, *, startup_without_waiting: bool = False, verbose_mode: bool = False
    ) -> colrev.env.local_index.LocalIndex:
        """Get a local-index object"""

        import colrev.env.local_index

        return colrev.env.local_index.LocalIndex(
            startup_without_waiting=startup_without_waiting, verbose_mode=verbose_mode
        )

    @classmethod
    def get_package_manager(  # type: ignore
        cls, **kwargs
    ) -> colrev.env.package_manager.PackageManager:
        """Get a package manager object"""

        import colrev.env.package_manager

        return colrev.env.package_manager.PackageManager(**kwargs)

    @classmethod
    def get_grobid_service(cls) -> colrev.env.grobid_service.GrobidService:
        """Get a grobid service object"""
        import colrev.env.grobid_service

        environment_manager = cls.get_environment_manager()
        return colrev.env.grobid_service.GrobidService(
            environment_manager=environment_manager
        )

    def get_tei(
        self, *, pdf_path: Path = None, tei_path: Path = None
    ) -> colrev.env.tei_parser.TEIParser:  # type: ignore
        """Get a tei object"""

        import colrev.env.tei_parser

        return colrev.env.tei_parser.TEIParser(
            environment_manager=self.environment_manager,
            pdf_path=pdf_path,
            tei_path=tei_path,
        )

    @classmethod
    def get_environment_manager(
        cls,
    ) -> colrev.env.environment_manager.EnvironmentManager:
        """Get an environment manager"""
        import colrev.env.environment_manager

        return colrev.env.environment_manager.EnvironmentManager()

    @classmethod
    def get_cached_session(cls) -> requests_cache.CachedSession:
        """Get a cached session"""

        return requests_cache.CachedSession(
            str(colrev.env.environment_manager.EnvironmentManager.cache_path),
            backend="sqlite",
            expire_after=timedelta(days=30),
        )

    @classmethod
    def get_zotero_translation_service(
        cls,
    ) -> colrev.env.zotero_translation_service.ZoteroTranslationService:
        """Get the zotero-translation service object"""
        import colrev.env.zotero_translation_service

        environment_manager = cls.get_environment_manager()

        return colrev.env.zotero_translation_service.ZoteroTranslationService(
            environment_manager=environment_manager
        )

    def get_screenshot_service(self) -> colrev.env.screenshot_service.ScreenshotService:
        """Get the screenshot-service object"""
        import colrev.env.screenshot_service

        return colrev.env.screenshot_service.ScreenshotService(review_manager=self)

    def get_pdf_hash_service(self) -> colrev.env.pdf_hash_service.PDFHashService:
        """Get the pdf-hash-service object"""
        import colrev.env.pdf_hash_service

        return colrev.env.pdf_hash_service.PDFHashService(review_manager=self)

    @classmethod
    def get_resources(cls) -> colrev.env.resources.Resources:
        """Get a resources object"""
        import colrev.env.resources

        return colrev.env.resources.Resources()

    @classmethod
    def get_init_operation(
        cls,
        review_type: str,
        example: bool = False,
        local_pdf_collection: bool = False,
    ) -> colrev.ops.init.Initializer:
        """Get an init operation object"""
        import colrev.ops.init

        return colrev.ops.init.Initializer(
            review_type=review_type,
            example=example,
            local_pdf_collection=local_pdf_collection,
        )

    @classmethod
    def get_sync_operation(cls) -> colrev.ops.sync.Sync:
        """Get a sync operation object"""
        import colrev.ops.sync

        return colrev.ops.sync.Sync()

    @classmethod
    def get_clone_operation(cls, *, git_url: str) -> colrev.ops.clone.Clone:
        """Get a clone operation object"""
        import colrev.ops.clone

        return colrev.ops.clone.Clone(git_url=git_url)

    def get_search_operation(
        self, *, notify_state_transition_operation: bool = True
    ) -> colrev.ops.search.Search:
        """Get a search operation object"""
        import colrev.ops.search

        return colrev.ops.search.Search(
            review_manager=self,
            notify_state_transition_operation=notify_state_transition_operation,
        )

    def get_load_operation(
        self, notify_state_transition_operation: bool = True
    ) -> colrev.ops.load.Load:
        """Get a load operation object"""
        import colrev.ops.load

        return colrev.ops.load.Load(
            review_manager=self,
            notify_state_transition_operation=notify_state_transition_operation,
        )

    def get_prep_operation(
        self,
        *,
        notify_state_transition_operation: bool = True,
        retrieval_similarity: float = 1.0,
    ) -> colrev.ops.prep.Prep:
        """Get a prep operation object"""
        import colrev.ops.prep

        return colrev.ops.prep.Prep(
            review_manager=self,
            notify_state_transition_operation=notify_state_transition_operation,
            retrieval_similarity=retrieval_similarity,
        )

    def get_prep_man_operation(
        self, *, notify_state_transition_operation: bool = True
    ) -> colrev.ops.prep_man.PrepMan:
        """Get a prep-man operation object"""
        import colrev.ops.prep_man

        return colrev.ops.prep_man.PrepMan(
            review_manager=self,
            notify_state_transition_operation=notify_state_transition_operation,
        )

    def get_dedupe_operation(
        self, *, notify_state_transition_operation: bool = True
    ) -> colrev.ops.dedupe.Dedupe:
        """Get a dedupe operation object"""
        import colrev.ops.dedupe

        return colrev.ops.dedupe.Dedupe(
            review_manager=self,
            notify_state_transition_operation=notify_state_transition_operation,
        )

    def get_prescreen_operation(
        self, *, notify_state_transition_operation: bool = True
    ) -> colrev.ops.prescreen.Prescreen:
        """Get a prescreen operation object"""

        import colrev.ops.prescreen

        return colrev.ops.prescreen.Prescreen(
            review_manager=self,
            notify_state_transition_operation=notify_state_transition_operation,
        )

    def get_pdf_get_operation(
        self, *, notify_state_transition_operation: bool = True
    ) -> colrev.ops.pdf_get.PDFGet:
        """Get a pdf-get operation object"""
        import colrev.ops.pdf_get

        return colrev.ops.pdf_get.PDFGet(
            review_manager=self,
            notify_state_transition_operation=notify_state_transition_operation,
        )

    def get_pdf_get_man_operation(
        self, *, notify_state_transition_operation: bool = True
    ) -> colrev.ops.pdf_get_man.PDFGetMan:
        """Get a pdf-get-man operation object"""
        import colrev.ops.pdf_get_man

        return colrev.ops.pdf_get_man.PDFGetMan(
            review_manager=self,
            notify_state_transition_operation=notify_state_transition_operation,
        )

    def get_pdf_prep_operation(
        self, *, reprocess: bool = False, notify_state_transition_operation: bool = True
    ) -> colrev.ops.pdf_prep.PDFPrep:
        """Get a pdfprep operation object"""
        import colrev.ops.pdf_prep

        return colrev.ops.pdf_prep.PDFPrep(
            review_manager=self,
            reprocess=reprocess,
            notify_state_transition_operation=notify_state_transition_operation,
        )

    def get_pdf_prep_man_operation(
        self, *, notify_state_transition_operation: bool = True
    ) -> colrev.ops.pdf_prep_man.PDFPrepMan:
        """Get a pdf-prep-man operation object"""
        import colrev.ops.pdf_prep_man

        return colrev.ops.pdf_prep_man.PDFPrepMan(
            review_manager=self,
            notify_state_transition_operation=notify_state_transition_operation,
        )

    def get_screen_operation(
        self, *, notify_state_transition_operation: bool = True
    ) -> colrev.ops.screen.Screen:
        """Get a screen operation object"""
        import colrev.ops.screen

        return colrev.ops.screen.Screen(
            review_manager=self,
            notify_state_transition_operation=notify_state_transition_operation,
        )

    def get_data_operation(
        self, *, notify_state_transition_operation: bool = True
    ) -> colrev.ops.data.Data:
        """Get a data operation object"""
        import colrev.ops.data

        return colrev.ops.data.Data(
            review_manager=self,
            notify_state_transition_operation=notify_state_transition_operation,
        )

    def get_status_operation(self) -> colrev.ops.status.Status:
        """Get a status operation object"""

        import colrev.ops.status

        return colrev.ops.status.Status(review_manager=self)

    def get_validate_operation(self) -> colrev.ops.validate.Validate:
        """Get a validate operation object"""
        import colrev.ops.validate

        return colrev.ops.validate.Validate(review_manager=self)

    def get_trace_operation(self) -> colrev.ops.trace.Trace:
        """Get a trace operation object"""
        import colrev.ops.trace

        return colrev.ops.trace.Trace(review_manager=self)

    def get_distribute_operation(self) -> colrev.ops.distribute.Distribute:
        """Get a distribute operation object"""

        import colrev.ops.distribute

        return colrev.ops.distribute.Distribute(review_manager=self)

    def get_push_operation(self, **kwargs) -> colrev.ops.push.Push:  # type: ignore
        """Get a push operation object"""

        import colrev.ops.push

        return colrev.ops.push.Push(review_manager=self, **kwargs)

    def get_pull_operation(self) -> colrev.ops.pull.Pull:
        """Get a pull operation object"""

        import colrev.ops.pull

        return colrev.ops.pull.Pull(review_manager=self)

    def get_service_operation(self) -> colrev.service.Service:
        """Get a service operation object"""

        import colrev.service

        return colrev.service.Service(review_manager=self)

    def get_search_sources(self) -> colrev.ops.search_sources.SearchSources:
        """Get a SearchSources object"""

        import colrev.ops.search_sources

        return colrev.ops.search_sources.SearchSources(review_manager=self)

    def get_review_types(
        self, *, review_type: str = None
    ) -> colrev.ops.review_types.ReviewTypes:
        """Get a ReviewTypes object"""
        import colrev.ops.review_types

        return colrev.ops.review_types.ReviewTypes(
            review_manager=self, review_type=review_type
        )

    def get_review_manager(
        self,
        *,
        path_str: str = None,
        force_mode: bool = False,
        verbose_mode: bool = False,
    ) -> ReviewManager:
        """Get a ReviewManager object"""
        return type(self)(
            path_str=path_str, force_mode=force_mode, verbose_mode=verbose_mode
        )


if __name__ == "__main__":
    pass
