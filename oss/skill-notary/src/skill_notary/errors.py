"""Errors with the CLI exit code they map to (documented in README.md, "Exit codes")."""

from __future__ import annotations

EXIT_OK = 0
EXIT_FINDINGS = 1  # scan: findings at or above --fail-on
EXIT_USAGE = 2  # bad input, skill not found, already installed
EXIT_BLOCKED = 3  # install: verdict dangerous or not_scanned
EXIT_APPROVAL = 4  # install: approval missing, rejected or for other content
EXIT_VERIFY = 5  # verify: drift, tampered lock or audit log
EXIT_ENGINE = 6  # fetch or scan engine failed (no verdict)


class NotaryError(Exception):
    exit_code = EXIT_USAGE

    def __init__(self, message: str, exit_code: int | None = None) -> None:
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class UsageError(NotaryError):
    exit_code = EXIT_USAGE


class FetchError(NotaryError):
    exit_code = EXIT_ENGINE


class EngineError(NotaryError):
    exit_code = EXIT_ENGINE


class BlockedError(NotaryError):
    exit_code = EXIT_BLOCKED


class ApprovalError(NotaryError):
    exit_code = EXIT_APPROVAL


class VerifyError(NotaryError):
    exit_code = EXIT_VERIFY
