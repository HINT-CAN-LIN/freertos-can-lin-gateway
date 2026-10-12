"""GUI 실행 및 선택적 의존성 안내."""
import argparse
import sys


GUI_DEPENDENCY_ERROR = (
    "GUI dependency unavailable: PySide6 is missing or could not be loaded.\n"
    "Install with pip install -e '.[gui]' from tools/diagnostic_GUI in the active environment."
)
WINDOWS_ERROR_TITLE = "PC Diagnostic Tool"
MB_OK = 0x00000000
MB_ICONERROR = 0x00000010


def show_windows_error(message):
    # Qt 설치 여부와 무관한 Windows API를 이 함수 안에서만 읽어온다.
    import ctypes
    message_box = ctypes.WinDLL("user32", use_last_error=True).MessageBoxW
    message_box.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
    message_box.restype = ctypes.c_int
    if message_box(None, message, WINDOWS_ERROR_TITLE, MB_OK | MB_ICONERROR) == 0:
        raise OSError(ctypes.get_last_error(), "Windows error notice failed")


def report_dependency_error():
    # 예외 원문에는 내부 경로가 들어갈 수 있으므로 고정된 원인/설치 안내만 표시한다.
    if sys.stderr is not None:
        try:
            print(GUI_DEPENDENCY_ERROR, file=sys.stderr)
            return True
        except Exception:
            # 고장 난 콘솔은 Windows 안내로 한 번만 전환하며 출력 재시도는 하지 않는다.
            if sys.platform != "win32":
                return False
    if sys.platform == "win32":
        try:
            show_windows_error(GUI_DEPENDENCY_ERROR)
            return True
        except Exception:
            # 안내 자체 실패를 False로 반환하고 main은 종료 코드 1로 안전하게 끝낸다.
            return False
    return False


def main(argv=None):
    # 도움말은 Qt 설치 없이도 확인할 수 있도록 import 전에 처리한다.
    parser = argparse.ArgumentParser(description="PC Diagnostic Tool - Mock / DEMO ONLY")
    parser.parse_args(argv)
    try:
        from PySide6.QtWidgets import QApplication
        from .window import MainWindow
    except ImportError:
        report_dependency_error()
        return 1
    # 통신 backend 선택은 제공하지 않으며 실제 CAN 송신은 연결하지 않는다.
    app = QApplication([sys.argv[0]])
    window = MainWindow()
    window.show()
    return app.exec()
