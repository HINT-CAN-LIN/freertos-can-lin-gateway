import builtins
from dataclasses import FrozenInstanceError

import pytest

from pc_diagnostic import DbcLoader, DbcLoadError, DbcLoadState, DbcLookupError
from pc_diagnostic.cli import main


def test_load_status_and_lookup(dbc_loader, synthetic_dbc_path):
    status = dbc_loader.status
    assert status.state is DbcLoadState.LOADED and dbc_loader.is_loaded
    assert status.path == synthetic_dbc_path.resolve()
    assert status.message_count == 3 and status.error is None
    message = dbc_loader.get_message_by_name("TestOnlySample")
    assert dbc_loader.get_message_by_id(1617) is message
    assert message.length == 4
    assert message.signals[0].scale == 0.25
    with pytest.raises(FrozenInstanceError):
        status.error = "mutated"


def test_standard_and_extended_lookup_isolation(dbc_loader):
    standard = dbc_loader.get_message_by_id(1617)
    extended = dbc_loader.get_message_by_id(1617, is_extended_id=True)
    assert standard.name == "TestOnlySample"
    assert extended.name == "TestOnlyExtended" and extended.is_extended_frame


def test_unloaded_lookup():
    loader = DbcLoader()
    assert loader.status.state is DbcLoadState.UNLOADED
    assert not loader.is_loaded
    with pytest.raises(DbcLookupError, match="not loaded"):
        loader.get_message_by_name("TestOnlySample")
    with pytest.raises(DbcLookupError):
        loader.get_message_by_id(1617)


@pytest.mark.parametrize("kind", ["missing", "directory", "malformed", "empty"])
def test_failed_load_clears_old_database(dbc_loader, tmp_path, kind):
    path = tmp_path / "bad.dbc"
    if kind == "directory":
        path.mkdir()
    elif kind == "malformed":
        path.write_text("this is not a DBC", encoding="utf-8")
    elif kind == "empty":
        path.write_text('VERSION "TEST ONLY empty"\nNS_ :\nBS_:\nBU_: Test\n', encoding="utf-8")
    with pytest.raises(DbcLoadError, match="DBC load failed"):
        dbc_loader.load(path)
    assert not dbc_loader.is_loaded
    assert dbc_loader.status.state is DbcLoadState.ERROR
    assert dbc_loader.status.message_count == 0 and dbc_loader.status.error
    with pytest.raises(DbcLookupError):
        dbc_loader.get_message_by_id(1617)


def test_retry_after_load_error(synthetic_dbc_path, tmp_path):
    loader = DbcLoader()
    with pytest.raises(DbcLoadError):
        loader.load(tmp_path / "missing.dbc")
    loader.load(synthetic_dbc_path)
    assert loader.is_loaded and loader.status.error is None


@pytest.mark.parametrize("lookup", [lambda db: db.get_message_by_name("NotDefined"),
                                    lambda db: db.get_message_by_id(0x7FE),
                                    lambda db: db.get_message_by_id(True),
                                    lambda db: db.get_message_by_id(1617, is_extended_id=1)])
def test_unknown_or_invalid_lookup(dbc_loader, lookup):
    with pytest.raises(DbcLookupError):
        lookup(dbc_loader)


@pytest.mark.parametrize("duplicate", ["name", "id"])
def test_ambiguous_definitions_rejected(synthetic_dbc_path, tmp_path, duplicate):
    text = synthetic_dbc_path.read_text(encoding="utf-8")
    if duplicate == "name":
        text = text.replace("TestOnlyExtended:", "TestOnlySample:")
    else:
        text = text.replace("BO_ 1618", "BO_ 1617")
    path = tmp_path / "test_only_ambiguous.dbc"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(DbcLoadError, match="duplicate"):
        DbcLoader().load(path)


def test_dependency_is_optional_for_raw_mode(monkeypatch, synthetic_dbc_path, capsys):
    original_import = builtins.__import__

    def missing_can_tools(name, *args, **kwargs):
        if name == "cantools":
            raise ImportError("simulated missing optional dependency")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_can_tools)
    with pytest.raises(DbcLoadError, match="install"):
        DbcLoader().load(synthetic_dbc_path)
    assert main(["monitor", "--duration", "0"]) == 0
    assert "Captured 0" in capsys.readouterr().err
