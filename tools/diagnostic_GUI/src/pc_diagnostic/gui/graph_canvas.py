"""기존 QtGui QPainter로 유한 Signal snapshot을 그린다. 외부 plotting 의존성 없음."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

PLOT_MIN_HEIGHT = 220
PLOT_LEFT = 90
PLOT_TOP = 35
PLOT_RIGHT = 25
PLOT_BOTTOM = 55
GRID_DIVISIONS = 4
EQUAL_VALUE_PADDING = 0.05


class GraphCanvas(QWidget):
    def __init__(self, parent=None):
        # Snapshot만 표시하고 Transport/Decode/Cache는 참조하지 않는다.
        super().__init__(parent)
        self.samples = ()
        self.setMinimumHeight(PLOT_MIN_HEIGHT)

    def set_samples(self, samples):
        # 호출은 GUI render timer에서만 하며 repaint 요청은 Qt가 병합한다.
        self.samples = tuple(samples)
        self.update()

    def paintEvent(self, event):
        # Qt 필수 override 예외. QWidget painting은 GUI 메인 스레드만 수행한다.
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(self.rect(), QColor("#101a28"))
            plot = QRectF(PLOT_LEFT, PLOT_TOP, max(1, self.width()-PLOT_LEFT-PLOT_RIGHT),
                          max(1, self.height()-PLOT_TOP-PLOT_BOTTOM))
            painter.setPen(QPen(QColor("#33445c"), 1))
            for i in range(GRID_DIVISIONS + 1):
                y = plot.top() + plot.height()*i/GRID_DIVISIONS
                painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.drawRect(plot)
            painter.setPen(QColor("#dbe7fa"))
            painter.drawText(QRectF(plot.left(), self.height()-PLOT_BOTTOM+20, plot.width(), 25),
                             Qt.AlignmentFlag.AlignCenter, "Elapsed RX timestamp (s) — first retained sample = 0")
            if not self.samples:
                painter.drawText(plot, Qt.AlignmentFlag.AlignCenter, "No plotted samples")
                return
            first, last = self.samples[0], self.samples[-1]
            elapsed = last.timestamp - first.timestamp
            span = elapsed if elapsed > 0 else 1.0
            # 큰 유한 값의 max-min overflow를 피하기 위해 좌표 계산만 정규화한다.
            scale = max(1.0, *(abs(float(s.value)) for s in self.samples))
            values = [float(s.value)/scale for s in self.samples]
            low, high = min(values), max(values)
            if low == high:
                low -= EQUAL_VALUE_PADDING
                high += EQUAL_VALUE_PADDING
            painter.drawText(QRectF(0, plot.top()-10, PLOT_LEFT-8, 25), Qt.AlignmentFlag.AlignRight,
                             f"{max(s.value for s in self.samples):.5g}")
            painter.drawText(QRectF(0, plot.bottom()-15, PLOT_LEFT-8, 25), Qt.AlignmentFlag.AlignRight,
                             f"{min(s.value for s in self.samples):.5g}")
            painter.drawText(QRectF(plot.left(), 5, plot.width(), 25), Qt.AlignmentFlag.AlignLeft,
                             "Value" + (f" [{first.unit}]" if first.unit else " [unit not defined]"))
            painter.drawText(QRectF(plot.left(), plot.bottom()+5, 70, 20), "0")
            painter.drawText(QRectF(plot.right()-90, plot.bottom()+5, 90, 20),
                             Qt.AlignmentFlag.AlignRight, f"{elapsed:.5g}")
            painter.setClipRect(plot.adjusted(-2, -2, 2, 2))
            painter.setPen(QPen(QColor("#45d9ed"), 2))
            path = QPainterPath()
            previous_segment = None
            for sample, value in zip(self.samples, values):
                x = plot.left() + (sample.timestamp-first.timestamp)/span*plot.width()
                y = plot.bottom() - (value-low)/(high-low)*plot.height()
                point = QPointF(x, y)
                if sample.segment != previous_segment:
                    path.moveTo(point)
                else:
                    path.lineTo(point)
                painter.drawEllipse(point, 2, 2)
                previous_segment = sample.segment
            painter.drawPath(path)
        finally:
            # 조기 return/paint 오류에도 painter 리소스를 반드시 해제한다.
            painter.end()
