import logging

from aqt.qt import (
    QLabel,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect,
    QFont,
    Qt,
    QPoint,
    QColor,
    QSequentialAnimationGroup,
    QPauseAnimation,
    QParallelAnimationGroup,
    QRect,
)

logger = logging.getLogger(__name__)

TIER_COLORS = {
    0: '#FFFFFF',
    1: '#FFD700',
    2: '#FF8C00',
    3: '#FF2D2D',
}

TIER_NAMES = {
    1: 'ON FIRE',
    2: 'UNSTOPPABLE',
    3: 'GODLIKE',
}


class VisualEffects:
    def __init__(self, mw):
        self._mw = mw
        self._combo_label = None
        self._flash_label = None
        self._center_label = None
        self._combo_hide_timer = None
        self._active_anims = []
        self.enabled = True

    @property
    def _parent(self):
        try:
            if self._mw and hasattr(self._mw, 'web') and self._mw.web:
                return self._mw.web
        except Exception:
            pass
        return self._mw

    def show_combo(self, streak, tier):
        if not self.enabled or not self._parent:
            return
        self._cleanup_label(self._combo_label)

        color = TIER_COLORS.get(tier, '#FFFFFF')
        size = min(28 + tier * 6, 46)

        label = QLabel(self._parent)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.setStyleSheet(f'''
            QLabel {{
                color: {color};
                font-size: {size}px;
                font-weight: 900;
                font-family: "SF Pro Display", "Helvetica Neue", "Arial Black", sans-serif;
                background: rgba(0, 0, 0, 0.5);
                border-radius: 8px;
                padding: 8px 16px;
            }}
        ''')
        label.setText(f'{streak}x')
        label.adjustSize()

        shadow = QGraphicsDropShadowEffect(label)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(color))
        label.setGraphicsEffect(shadow)

        pw = self._parent.width()
        label.move(pw - label.width() - 20, 20)
        label.show()
        label.raise_()
        self._combo_label = label

        self._animate_pop(label)

        if self._combo_hide_timer:
            self._combo_hide_timer.stop()
        self._combo_hide_timer = QTimer()
        self._combo_hide_timer.setSingleShot(True)
        self._combo_hide_timer.timeout.connect(lambda: self._cleanup_label(self._combo_label))
        self._combo_hide_timer.start(3000)

    def show_tier_up(self, tier, streak):
        if not self.enabled or not self._parent:
            return

        name = TIER_NAMES.get(tier, f'{streak}x COMBO')
        color = TIER_COLORS.get(tier, '#FFD700')
        self._show_center_text(f'{streak}x {name}!', color, size=42, duration=1800)

    def show_milestone(self, count):
        if not self.enabled or not self._parent:
            return
        self._show_center_text(f'{count} CARDS!', '#00FFAA', size=48, duration=2200)

    def show_combo_break(self, lost_streak):
        if not self.enabled or not self._parent:
            return

        self._flash_screen('#FF0000', duration=400)

        if lost_streak >= 5:
            self._show_center_text(
                f'COMBO BREAK\n-{lost_streak}x-',
                '#FF4444', size=38, duration=1500
            )

    def show_fail(self):
        if not self.enabled or not self._parent:
            return
        self._flash_screen('#FF0000', duration=250)

    def _show_center_text(self, text, color, size=40, duration=1800):
        self._cleanup_label(self._center_label)

        parent = self._parent
        if not parent:
            return

        label = QLabel(parent)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f'''
            QLabel {{
                color: {color};
                font-size: {size}px;
                font-weight: 900;
                font-family: "SF Pro Display", "Helvetica Neue", "Arial Black", sans-serif;
                background: rgba(0, 0, 0, 0.6);
                border-radius: 12px;
                padding: 16px 32px;
            }}
        ''')
        label.setText(text)
        label.adjustSize()

        pw, ph = parent.width(), parent.height()
        label.move((pw - label.width()) // 2, (ph - label.height()) // 2 - 40)
        label.show()
        label.raise_()
        self._center_label = label

        opacity = QGraphicsOpacityEffect(label)
        label.setGraphicsEffect(opacity)

        group = QSequentialAnimationGroup(label)

        fade_in = QPropertyAnimation(opacity, b'opacity')
        fade_in.setDuration(150)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(fade_in)

        group.addPause(duration - 500)

        fade_out = QPropertyAnimation(opacity, b'opacity')
        fade_out.setDuration(350)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        group.addAnimation(fade_out)

        group.finished.connect(lambda: self._cleanup_label(label))
        self._active_anims.append(group)
        group.finished.connect(lambda: self._remove_anim(group))
        group.start()

        self._animate_scale_bounce(label)

    def _flash_screen(self, color, duration=300):
        self._cleanup_label(self._flash_label)

        label = QLabel(self._parent)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.setStyleSheet(f'background: {color};')
        label.setGeometry(0, 0, self._parent.width(), self._parent.height())
        label.show()
        label.raise_()
        self._flash_label = label

        opacity = QGraphicsOpacityEffect(label)
        label.setGraphicsEffect(opacity)

        anim = QPropertyAnimation(opacity, b'opacity')
        anim.setDuration(duration)
        anim.setStartValue(0.35)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.finished.connect(lambda: self._cleanup_label(label))
        self._active_anims.append(anim)
        anim.finished.connect(lambda: self._remove_anim(anim))
        anim.start()

    def _animate_pop(self, label):
        start_pos = label.pos()
        anim = QPropertyAnimation(label, b'pos')
        anim.setDuration(200)
        anim.setStartValue(QPoint(start_pos.x(), start_pos.y() - 8))
        anim.setEndValue(start_pos)
        anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._active_anims.append(anim)
        anim.finished.connect(lambda: self._remove_anim(anim))
        anim.start()

    def _animate_scale_bounce(self, label):
        geo = label.geometry()
        cx, cy = geo.center().x(), geo.center().y()
        w, h = geo.width(), geo.height()

        small = QRect(cx - w // 4, cy - h // 4, w // 2, h // 2)
        big = QRect(cx - int(w * 0.55), cy - int(h * 0.55), int(w * 1.1), int(h * 1.1))

        group = QSequentialAnimationGroup(label)

        expand = QPropertyAnimation(label, b'geometry')
        expand.setDuration(120)
        expand.setStartValue(small)
        expand.setEndValue(big)
        expand.setEasingCurve(QEasingCurve.Type.OutQuad)
        group.addAnimation(expand)

        settle = QPropertyAnimation(label, b'geometry')
        settle.setDuration(180)
        settle.setStartValue(big)
        settle.setEndValue(geo)
        settle.setEasingCurve(QEasingCurve.Type.OutBack)
        group.addAnimation(settle)

        self._active_anims.append(group)
        group.finished.connect(lambda: self._remove_anim(group))
        group.start()

    def _cleanup_label(self, label):
        if label is not None:
            try:
                label.hide()
                label.deleteLater()
            except RuntimeError:
                pass
        if label is self._combo_label:
            self._combo_label = None
        elif label is self._flash_label:
            self._flash_label = None
        elif label is self._center_label:
            self._center_label = None

    def _remove_anim(self, anim):
        try:
            self._active_anims.remove(anim)
        except ValueError:
            pass

    def cleanup(self):
        for label in (self._combo_label, self._flash_label, self._center_label):
            self._cleanup_label(label)
        self._active_anims.clear()
