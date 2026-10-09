"""Tests for the pure parsing helpers in scheduler.py. No database needed.

Known bugs are written as the behaviour we want and marked xfail(strict=True).
They keep the suite green while the bug exists, and fail loudly once it's fixed
so the marker gets removed.
"""
from datetime import datetime

import pytest

from zabmap_api.scheduler import (
    extract_backup_type,
    extract_date_from_snapshot_name,
    parse_server_prop,
)


class TestParseServerProp:
    def test_single_entry(self):
        assert parse_server_prop("hostB:pool-zab") == [("hostB", "pool/zab")]

    def test_multiple_entries(self):
        assert parse_server_prop("hostB:pool-zab,hostC:pool-zas") == [
            ("hostB", "pool/zab"),
            ("hostC", "pool/zas"),
        ]

    def test_empty_property_means_no_replicas(self):
        # update_parents passes "" when a filesystem has no zab:server property.
        assert parse_server_prop("") == []

    def test_localhost_entry_has_no_colon_in_host(self):
        # This is why update_parents' `host == "localhost:"` check can never
        # match (F04): the parsed host is "localhost", without the colon.
        assert parse_server_prop("localhost:raid-r1") == [("localhost", "raid/r1")]

    def test_every_dash_becomes_a_slash(self):
        # Current behaviour, pinned. A dataset name that really contains a dash
        # gets mangled (F06), but whether that can happen under the zab naming
        # convention is unconfirmed, so this isn't marked as a bug yet.
        assert parse_server_prop("hostB:pool-zab-my-data") == [
            ("hostB", "pool/zab/my/data")
        ]

    @pytest.mark.xfail(
        strict=True,
        reason="F05: one malformed entry discards every entry of the property",
    )
    def test_malformed_entry_keeps_the_valid_ones(self):
        assert parse_server_prop("hostB:pool-zab,garbage") == [("hostB", "pool/zab")]

    def test_malformed_entry_currently_discards_everything(self):
        # Current behaviour behind F05: the filesystem silently looks like it
        # has 0 expected replicas.
        assert parse_server_prop("hostB:pool-zab,garbage") == []
        assert parse_server_prop("hostB:pool-zab,hostC:pool:extra") == []


class TestExtractDateFromSnapshotName:
    def test_trailing_timestamp(self):
        assert extract_date_from_snapshot_name(
            "raid/projects@zab-20260611143000"
        ) == datetime(2026, 6, 11, 14, 30, 0)

    @pytest.mark.parametrize("empty", [None, ""])
    def test_no_snapshot(self, empty):
        assert extract_date_from_snapshot_name(empty) is None

    @pytest.mark.parametrize(
        "name",
        [
            "raid/projects@manual-backup",  # no timestamp at all
            "raid/projects@zab-20260611",  # date only
            "raid/projects@zab-20260611143000-extra",  # timestamp not at the end
        ],
    )
    def test_names_without_trailing_14_digit_timestamp(self, name):
        # Current behaviour, pinned (F08): these count as "no snapshot", which
        # makes their replicas show out of sync.
        assert extract_date_from_snapshot_name(name) is None

    def test_impossible_date_is_none(self):
        # Fourteen digits, but month 13 doesn't exist.
        assert extract_date_from_snapshot_name("fs@zab-20261311143000") is None


class TestExtractBackupType:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("pool/zab/projects/foo", "zab"),
            ("pool/zas/projects/foo", "zas"),
            ("raid/projects/foo", None),
            ("", None),
        ],
    )
    def test_detects_type_from_path(self, path, expected):
        assert extract_backup_type(path) == expected

    def test_needs_slashes_on_both_sides(self):
        # "/zab/" must be a whole path component, so these aren't backups.
        assert extract_backup_type("zab/projects") is None
        assert extract_backup_type("pool/zabbix/projects") is None
