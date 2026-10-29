"""Qt를 삭제하지 않고 GUI 의존성 오류 안내를 검증한다."""
import builtins
import ctypes

import pytest
from pc_diagnostic.gui import app as gui_app


@pytest.fixture
def missing_qt(monkeypatch):
    # import 단계에서만 실패를 주입하므로 설치된 PySide6를 손상시키지 않는다.
    original_import = builtins.__import__
    def blocked_import(name, *args, **kwargs):
        # 실제 경로가 포함된 import 오류도 사용자 안내에 노출하지 않아야 한다.
        if name == "PySide6.QtWidgets":
            raise ImportError("private-path/test-secret")
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", blocked_import)


def test_missing_qt_console_message_is_clear_and_sanitized(missing_qt, capsys):
    # 콘솔에서는 설치 방법을 stderr로 전달하고 내부 경로를 숨긴다.
    assert gui_app.main([]) == 1
    message = capsys.readouterr().err
    assert "PySide6" in message and "Install with" in message
    assert "pip install -e '.[gui]'" in message
    assert "private-path" not in message and "test-secret" not in message


def test_missing_qt_without_console_uses_windows_notice(missing_qt, monkeypatch):
    # stdout/stderr가 없는 GUI에서도 Windows 안내를 정확히 한 번 호출한다.
    messages = []
    monkeypatch.setattr(gui_app.sys, "platform", "win32")
    monkeypatch.setattr(gui_app.sys, "stdout", None)
    monkeypatch.setattr(gui_app.sys, "stderr", None)
    monkeypatch.setattr(gui_app, "show_windows_error", messages.append, raising=False)
    assert gui_app.main([]) == 1
    assert len(messages) == 1
    assert "PySide6" in messages[0] and "pip install -e '.[gui]'" in messages[0]
    assert "private-path" not in messages[0]


def test_notice_failure_exits_without_retry(missing_qt, monkeypatch):
    # Windows 안내 자체가 실패해도 예외 전파나 재귀 재시도를 하지 않는다.
    attempts = []
    def failed_notice(message):
        # API 실패를 모의하며 호출 횟수를 기록한다.
        attempts.append(message)
        raise OSError("test notice failure")
    monkeypatch.setattr(gui_app.sys, "platform", "win32")
    monkeypatch.setattr(gui_app.sys, "stdout", None)
    monkeypatch.setattr(gui_app.sys, "stderr", None)
    monkeypatch.setattr(gui_app, "show_windows_error", failed_notice, raising=False)
    assert gui_app.main([]) == 1
    assert len(attempts) == 1


def test_broken_console_falls_back_to_windows_notice(missing_qt, monkeypatch):
    # 닫히거나 고장 난 콘솔도 Windows 안내로 한 번만 전환한다.
    class BrokenStream:
        def write(self, value):
            # 실제 출력 실패를 주입한다.
            raise OSError("test console unavailable")
    messages = []
    monkeypatch.setattr(gui_app.sys, "platform", "win32")
    monkeypatch.setattr(gui_app.sys, "stderr", BrokenStream())
    monkeypatch.setattr(gui_app, "show_windows_error", messages.append, raising=False)
    assert gui_app.main([]) == 1
    assert len(messages) == 1


def test_non_windows_without_console_returns_notification_failure(monkeypatch):
    # Windows가 아닌 콘솔 없는 환경에서는 지원되지 않는 API를 호출하지 않는다.
    monkeypatch.setattr(gui_app.sys, "platform", "linux")
    monkeypatch.setattr(gui_app.sys, "stdout", None)
    monkeypatch.setattr(gui_app.sys, "stderr", None)
    assert gui_app.report_dependency_error() is False


@pytest.mark.parametrize("api_result", [1, 0])
def test_windows_notice_api_signature_and_failure(monkeypatch, api_result):
    # 실제 WinAPI를 띄우지 않고 wide 문자열/인수/실패 반환 처리를 검증한다.
    calls = []
    class FakeMessageBox:
        def __call__(self, *args):
            # 명시적 ctypes 시그니처를 설정한 뒤 API를 호출해야 한다.
            calls.append(args)
            return api_result
    class FakeUser32:
        MessageBoxW = FakeMessageBox()
    def fake_dll(name, **kwargs):
        # Windows 의존 함수가 Qt 없이 user32만 사용하도록 확인한다.
        assert name == "user32" and kwargs == {"use_last_error": True}
        return FakeUser32()
    monkeypatch.setattr(ctypes, "WinDLL", fake_dll, raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 5, raising=False)
    if api_result == 0:
        with pytest.raises(OSError):
            gui_app.show_windows_error("TEST ONLY notification")
    else:
        gui_app.show_windows_error("TEST ONLY notification")
    assert calls == [(None, "TEST ONLY notification", "PC Diagnostic Tool", 0x10)]
    assert FakeUser32.MessageBoxW.argtypes == [ctypes.c_void_p, ctypes.c_wchar_p,
                                               ctypes.c_wchar_p, ctypes.c_uint]
    assert FakeUser32.MessageBoxW.restype is ctypes.c_int
