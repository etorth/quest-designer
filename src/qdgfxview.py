# -*- coding: utf-8 -*-
"""Custom QGraphicsView subclass providing zoom controls for QuestDesigner.

Responsibilities:
- Ctrl + Mouse Wheel zooming
- Menu/shortcut invoked zoom in/out/reset/fit
- Clamped zoom range
- Normalization of transform to avoid floating point drift

Future enhancements (not implemented yet):
- Smooth animated zoom
- Zoom indicator signal
- Middle-mouse panning
"""
from __future__ import annotations

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtGui import QWheelEvent, QPainter, QTransform
from PySide6.QtCore import Qt, QRectF, Signal


class QD_GfxView(QGraphicsView):
    # Emitted with the new scale factor (1.0 == 100%)
    zoomChanged = Signal(float)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        # Use enum-scoped values for type-checker friendliness
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # Zoom parameters
        self._min_scale = 0.1
        self._max_scale = 5.0
        self._step_factor = 1.15  # incremental wheel/menu zoom factor

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
        return int(round(self.current_scale() * 100))

    # --- Internal helpers -------------------------------------------------
    def _apply_zoom(self, factor: float):
        if factor <= 0:
            return
        current = self.transform().m11()
        new_scale = current * factor
        if new_scale < self._min_scale or new_scale > self._max_scale:
            return
        self.scale(factor, factor)
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
            self.reset_zoom()
        elif cur > self._max_scale:
            self.reset_zoom()

    def _emit_zoom_changed(self):
        self.zoomChanged.emit(self.transform().m11())

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

__all__ = ["QD_GfxView"]
