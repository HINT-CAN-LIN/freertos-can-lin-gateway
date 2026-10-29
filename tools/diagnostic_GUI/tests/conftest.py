from pathlib import Path

import pytest

from pc_diagnostic import DbcCodec, DbcLoader


@pytest.fixture
def synthetic_dbc_path():
    return Path(__file__).parent / "fixtures" / "test_only.dbc"


@pytest.fixture
def dbc_loader(synthetic_dbc_path):
    return DbcLoader().load(synthetic_dbc_path)


@pytest.fixture
def dbc_codec(dbc_loader):
    return DbcCodec(dbc_loader)
