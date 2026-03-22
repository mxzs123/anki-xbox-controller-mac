import logging

from aqt import mw
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QComboBox,
    QSlider,
    QCheckBox,
    QPushButton,
    QFormLayout,
    QFileDialog,
    QGridLayout,
    Qt,
)

from .actions import AVAILABLE_ACTIONS
from .haptics import DEFAULT_PROFILES

logger = logging.getLogger(__name__)

BUTTON_LABELS = {
    'A': 'A 键',
    'B': 'B 键',
    'X': 'X 键',
    'Y': 'Y 键',
    'left_trigger': '左扳机 (LT)',
    'right_trigger': '右扳机 (RT)',
}


class ConfigDialog(QDialog):
    def __init__(self, config, sound_player=None, haptic_player=None, parent=None):
        super().__init__(parent or mw)
        self._config = config
        self._sound_player = sound_player
        self._haptic_player = haptic_player
        self._mapping_combos = {}
        self._sound_labels = {}
        self.setWindowTitle('Xbox Controller Settings')
        self.setMinimumWidth(480)
        self.setMinimumHeight(360)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        tabs.addTab(self._build_mapping_tab(), '按键映射')
        tabs.addTab(self._build_sound_tab(), '音效设置')
        tabs.addTab(self._build_haptics_tab(), '震动设置')

        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton('保存')
        save_btn.clicked.connect(self._save_and_close)
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _build_mapping_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(12)

        mapping = self._config.get('button_mapping', {})
        action_keys = list(AVAILABLE_ACTIONS.keys())
        action_labels = [f'{k} - {v}' for k, v in AVAILABLE_ACTIONS.items()]

        for btn_name, btn_label in BUTTON_LABELS.items():
            combo = QComboBox()
            for ak, al in zip(action_keys, action_labels):
                combo.addItem(al, ak)
            current_action = mapping.get(btn_name, 'none')
            idx = action_keys.index(current_action) if current_action in action_keys else len(action_keys) - 1
            combo.setCurrentIndex(idx)
            self._mapping_combos[btn_name] = combo
            layout.addRow(btn_label, combo)

        return widget

    def _build_sound_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._sound_enabled_cb = QCheckBox('启用音效反馈')
        self._sound_enabled_cb.setChecked(self._config.get('sounds', {}).get('enabled', True))
        layout.addWidget(self._sound_enabled_cb)

        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel('全局音量'))
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(int(self._config.get('sounds', {}).get('volume', 0.7) * 100))
        vol_layout.addWidget(self._volume_slider)
        layout.addLayout(vol_layout)

        profiles = self._config.get('sounds', {}).get('profiles', {})
        grid = QGridLayout()
        grid.addWidget(QLabel('动作'), 0, 0)
        grid.addWidget(QLabel('音效文件'), 0, 1)
        grid.addWidget(QLabel(''), 0, 2)
        grid.addWidget(QLabel(''), 0, 3)

        row = 1
        for action_name, action_label in AVAILABLE_ACTIONS.items():
            if action_name == 'none' or action_name == 'show_answer':
                continue

            grid.addWidget(QLabel(action_label), row, 0)

            path_label = QLabel(profiles.get(action_name, ''))
            path_label.setMinimumWidth(200)
            self._sound_labels[action_name] = path_label
            grid.addWidget(path_label, row, 1)

            browse_btn = QPushButton('浏览')
            browse_btn.setFixedWidth(60)
            browse_btn.clicked.connect(lambda checked, an=action_name: self._browse_sound(an))
            grid.addWidget(browse_btn, row, 2)

            test_btn = QPushButton('试听')
            test_btn.setFixedWidth(60)
            test_btn.clicked.connect(lambda checked, an=action_name: self._test_sound(an))
            grid.addWidget(test_btn, row, 3)

            row += 1

        layout.addLayout(grid)
        layout.addStretch()
        return widget

    def _build_haptics_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._haptics_enabled_cb = QCheckBox('启用震动反馈')
        haptics_config = self._config.get('haptics', {})
        self._haptics_enabled_cb.setChecked(haptics_config.get('enabled', True))
        layout.addWidget(self._haptics_enabled_cb)

        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel('震动强度'))
        self._intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self._intensity_slider.setRange(0, 100)
        self._intensity_slider.setValue(int(haptics_config.get('intensity_scale', 1.0) * 100))
        scale_layout.addWidget(self._intensity_slider)
        layout.addLayout(scale_layout)

        supported = self._haptic_player and self._haptic_player.is_supported
        status_label = QLabel('手柄震动: 已支持' if supported else '手柄震动: 未连接或不支持')
        layout.addWidget(status_label)

        test_btn = QPushButton('测试震动')
        test_btn.setEnabled(supported)
        test_btn.clicked.connect(self._test_haptic)
        layout.addWidget(test_btn)

        layout.addStretch()
        return widget

    def _test_haptic(self):
        if not self._haptic_player or not self._haptic_player.is_supported:
            return
        old_scale = self._haptic_player.intensity_scale
        self._haptic_player.intensity_scale = self._intensity_slider.value() / 100.0
        self._haptic_player.play_test()
        self._haptic_player.intensity_scale = old_scale

    def _test_sound(self, action_name):
        if not self._sound_player:
            return
        path = self._sound_labels[action_name].text()
        if path:
            old_vol = self._sound_player.volume
            self._sound_player.volume = self._volume_slider.value() / 100.0
            self._sound_player.play(path)
            self._sound_player.volume = old_vol

    def _browse_sound(self, action_name):
        path, _ = QFileDialog.getOpenFileName(
            self, '选择音效文件', '', 'Audio Files (*.wav *.aiff *.mp3);;All Files (*)'
        )
        if path:
            self._sound_labels[action_name].setText(path)

    def _save_and_close(self):
        mapping = {}
        for btn_name, combo in self._mapping_combos.items():
            mapping[btn_name] = combo.currentData()
        self._config['button_mapping'] = mapping

        sounds_config = {
            'enabled': self._sound_enabled_cb.isChecked(),
            'volume': self._volume_slider.value() / 100.0,
            'profiles': {},
        }
        for action_name, label in self._sound_labels.items():
            sounds_config['profiles'][action_name] = label.text()
        self._config['sounds'] = sounds_config

        haptics_config = self._config.get('haptics', {})
        haptics_config['enabled'] = self._haptics_enabled_cb.isChecked()
        haptics_config['intensity_scale'] = self._intensity_slider.value() / 100.0
        if 'profiles' not in haptics_config:
            haptics_config['profiles'] = dict(DEFAULT_PROFILES)
        self._config['haptics'] = haptics_config

        mw.addonManager.writeConfig(__name__.split('.')[0], self._config)
        logger.info('Xbox controller config saved')
        self.accept()
