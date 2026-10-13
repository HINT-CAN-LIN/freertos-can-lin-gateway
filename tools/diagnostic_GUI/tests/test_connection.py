"""Qt/Hardware 없이 연결 입력과 backend 의존성 안내를 검증한다."""
import pytest
from pc_diagnostic.gui.connection import ConnectionSettings, open_live_interface, require_live_dependencies
from pc_diagnostic.gui import connection
from pc_diagnostic.interfaces import CanInterfaceError


@pytest.mark.parametrize("settings", [
    ConnectionSettings(), ConnectionSettings("Live", "slcan", "COM_ACTUAL", 500000),
    ConnectionSettings("Live", "slcan", "COM_ACTUAL@115200", 500000),
    ConnectionSettings("Live", "gs_usb", 0, 500000),
])
def test_valid_explicit_settings(settings):
    # COM_ACTUAL은 실제 장치가 아닌 입력 검증용 문자열이다.
    assert settings.validate() is settings


@pytest.mark.parametrize("settings", [
    ConnectionSettings("Other"), ConnectionSettings("Live"),
    ConnectionSettings("Live", "unknown", "port", 500000),
    ConnectionSettings("Live", "slcan", "", 500000),
    ConnectionSettings("Live", "slcan", 0, 500000),
    ConnectionSettings("Live", "gs_usb", "0", 500000),
    ConnectionSettings("Live", "gs_usb", -1, 500000),
    ConnectionSettings("Live", "slcan", "port", None),
    ConnectionSettings("Live", "slcan", "port", 0),
    ConnectionSettings("Live", "slcan", "port", True),
])
def test_invalid_settings_do_not_open_bus(settings, monkeypatch):
    # 입력 검증 실패 전에 bus를 열거나 자동 Mock으로 전환하면 안 된다.
    monkeypatch.setattr(connection, "PythonCanInterface", lambda **kwargs: pytest.fail("bus opened"))
    with pytest.raises(ValueError):
        open_live_interface(settings)


@pytest.mark.parametrize("backend,module,install", [
    ("slcan", "can", "python-can"), ("slcan", "serial", "python-can[serial]"),
    ("gs_usb", "gs_usb", "python-can[gs-usb]"), ("gs_usb", "usb", "python-can[gs-usb]"),
])
def test_dependency_missing_is_explicit_without_install(backend, module, install, monkeypatch):
    # 개발 환경의 실제 패키지를 제거하지 않고 모듈 조회만 모의한다.
    monkeypatch.setattr(connection, "find_spec", lambda name: None if name == module else object())
    with pytest.raises(CanInterfaceError, match="Missing Live dependency") as error:
        require_live_dependencies(backend)
    assert module in str(error.value) and install in str(error.value)


def test_reuses_python_can_adapter_and_preserves_arguments(monkeypatch):
    # GUI 전용 Bus 구현이나 send 호출 없이 기존 Adapter에 그대로 위임한다.
    calls = []
    sentinel = object()
    monkeypatch.setattr(connection, "find_spec", lambda name: object())
    def adapter(**kwargs):
        # Backend 설정의 타입과 값을 기록한다.
        calls.append(kwargs)
        return sentinel
    monkeypatch.setattr(connection, "PythonCanInterface", adapter)
    settings = ConnectionSettings("Live", "gs_usb", 0, 500000)
    assert open_live_interface(settings) is sentinel
    assert calls == [{"interface": "gs_usb", "channel": 0, "bitrate": 500000}]
