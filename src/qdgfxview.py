# -*- coding: utf-8 -*-
"""Custom QGraphicsView subclass providing zoom controls for QuestDesigner.

Responsibilities:
- Ctrl + Mouse Wheel zooming
- Menu/shortcut invoked zoom in/out/reset/fit
- Clamped zoom range
- Normalization of transform to avoid floating point drift
- Ctrl + Left-button drag panning when clicking empty space with no active selection

Future enhancements (not implemented yet):
- Smooth animated zoom
- Zoom indicator signal
- Middle-mouse panning
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtGui import QWheelEvent, QPainter, QTransform, QMouseEvent, QCursor
from PySide6.QtCore import Qt, QRectF, Signal, QPoint


class QD_GfxView(QGraphicsView):
    # Emitted with the new scale factor (1.0 == 100%)
    zoom_changed = Signal(float)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        # Use enum-scoped values for type-checker friendliness
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # Zoom parameters (10% .. 500%)
        self._min_scale = 0.10  # 10%
        self._max_scale = 5.00  # 500%
        self._step_factor = 1.15

        # Panning state
        self._panning = False
        self._pan_last_pos: QPoint | None = None
        self._saved_drag_mode = self.dragMode()

    # --- Public API -------------------------------------------------------
    def zoom_in(self):
        self._apply_zoom(self._step_factor)

    def zoom_out(self):
        self._apply_zoom(1 / self._step_factor)

    def reset_zoom(self):
        # Reset to scale 1 preserving translation
        t = self.transform()
        current_scale = t.m11()
        if current_scale == 0:
            return
        self.scale(1 / current_scale, 1 / current_scale)
        self._normalize_transform()
        self._emit_zoom_changed()

    def fit_scene(self, margin: float = 50):
        # Fit the entire scene into view with an optional margin.
        scene = self.scene()
        if scene is None:
            return
        rect: QRectF = scene.sceneRect()
        if not rect.isValid():
            return
        # Add margin
        fitted = QRectF(rect)
        fitted.adjust(-margin, -margin, margin, margin)
        self.fitInView(fitted, Qt.AspectRatioMode.KeepAspectRatio)
        self._clamp_to_limits()
        self._normalize_transform()
        self._emit_zoom_changed()

    def current_scale(self) -> float:
        return self.transform().m11()

    def current_zoom_percent(self) -> int:
        # Clamp for safety against rounding drift
        pct = int(round(self.current_scale() * 100))
        if pct < int(self._min_scale * 100):
            pct = int(self._min_scale * 100)
        elif pct > int(self._max_scale * 100):
            pct = int(self._max_scale * 100)
        return pct

    # --- Internal helpers -------------------------------------------------
    def _apply_zoom(self, factor: float):
        if factor <= 0:
            return
        current = self.transform().m11()
        target = current * factor
        # Clamp target into allowed range
        if target < self._min_scale:
            target = self._min_scale
        elif target > self._max_scale:
            target = self._max_scale
        # Compute actual factor to reach clamped target
        actual_factor = target / current if current else 1.0
        # Avoid tiny useless adjustments
        if abs(actual_factor - 1.0) < 1e-6:
            return
        self.scale(actual_factor, actual_factor)
        self._normalize_transform()
        self._emit_zoom_changed()

    def _normalize_transform(self):
        # Keep uniform scaling (avoid shear) & limit precision drift.
        t = self.transform()
        sx = t.m11()
        sy = t.m22()
        # Average scales (should be near identical)
        uni = (sx + sy) / 2.0
        if uni == 0:
            return
        # Rebuild simplified transform (discard rotation/shear for now)
        self.setTransform(QTransform().scale(uni, uni))

    def _clamp_to_limits(self):
        cur = self.transform().m11()
        if cur < self._min_scale:
            factor = self._min_scale / cur if cur else 1.0
            self.scale(factor, factor)
        elif cur > self._max_scale:
            factor = self._max_scale / cur
            self.scale(factor, factor)

    def _emit_zoom_changed(self):
        self.zoom_changed.emit(self.transform().m11())

    # --- Panning helpers --------------------------------------------------
    def _start_panning(self, pos: QPoint):
        self._panning = True
        self._pan_last_pos = pos
        self._saved_drag_mode = self.dragMode()
        self.setDragMode(QGraphicsView.DragMode.NoDrag)  # suppress rubber band during panning
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def _end_panning(self):
        self._panning = False
        self._pan_last_pos = None
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.setDragMode(self._saved_drag_mode)

    # --- Events -----------------------------------------------------------
    def wheelEvent(self, event: QWheelEvent):  # Ctrl + Wheel zoom
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Only start panning if Ctrl is held, click is on empty space, and nothing is selected
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                item = self.itemAt(event.pos())
                scene = self.scene()
                has_selection = bool(scene and scene.selectedItems())
                if item is None and not has_selection:
                    self._start_panning(event.pos())
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        # Enforce Ctrl must remain held for panning; if released, stop panning immediately
        if self._panning and not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self._end_panning()
            # Fall through to allow normal processing (e.g., potential hover updates)
        if self._panning and self._pan_last_pos is not None:
            delta = event.pos() - self._pan_last_pos
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())
            self._pan_last_pos = event.pos()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._panning:
            self._end_panning()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyReleaseEvent(self, event):
        # If Ctrl released while panning (and user hasn't moved mouse yet), end panning immediately
        try:
            if self._panning and event.key() == Qt.Key.Key_Control:
                self._end_panning()
        except Exception:  # pragma: no cover - defensive
            pass
        super().keyReleaseEvent(event)

__all__ = ["QD_GfxView"]
