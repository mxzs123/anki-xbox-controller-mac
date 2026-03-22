import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)
_addon_dir = os.path.dirname(os.path.abspath(__file__))

REQUIRED_PACKAGES = [
    ('objc', 'pyobjc-core'),
    ('GameController', 'pyobjc-framework-GameController'),
    ('Foundation', 'pyobjc-framework-Cocoa'),
    ('CoreHaptics', 'pyobjc-framework-CoreHaptics'),
]


def _ensure_dependencies():
    missing = []
    for module_name, pip_name in REQUIRED_PACKAGES:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)
    if missing:
        logger.info('Installing missing dependencies: %s', missing)
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--quiet',
                '--disable-pip-version-check',
            ] + missing)
            logger.info('Dependencies installed successfully')
        except Exception as e:
            logger.error('Failed to install dependencies: %s', e)


_ensure_dependencies()

from aqt import mw, gui_hooks
from aqt.qt import QAction, QTimer
from aqt.utils import tooltip

from .controller import XboxController
from .sounds import SoundPlayer
from .haptics import HapticPlayer, DEFAULT_PROFILES
from .actions import execute_action
from .combo import ComboTracker
from .effects import VisualEffects

_xbox = None
_sound_player = None
_haptic_player = None
_combo_tracker = None
_visual_effects = None
_poll_timer = None
_config = None


def get_config():
    global _config
    _config = mw.addonManager.getConfig(__name__.split('.')[0]) or {}
    return _config


def on_controller_connect(gc_controller):
    try:
        name = str(gc_controller.vendorName() or 'Xbox Controller')
    except Exception:
        name = 'Xbox Controller'

    if _haptic_player:
        _haptic_player.attach(gc_controller)
        if _haptic_player.is_supported:
            tooltip(f'{name} 已连接 (震动已启用)', parent=mw)
        else:
            tooltip(f'{name} 已连接 (不支持震动)', parent=mw)
    else:
        tooltip(f'{name} 已连接', parent=mw)


def on_controller_disconnect(gc_controller):
    if _haptic_player:
        _haptic_player.detach()
    tooltip('手柄已断开', parent=mw)


def on_button_press(button_name):
    config = _config or get_config()
    mapping = config.get('button_mapping', {})
    action_name = mapping.get(button_name)

    if not action_name or action_name == 'none':
        return

    logger.debug('Button %s -> action %s', button_name, action_name)

    result = execute_action(action_name)

    if result == 'show_answer':
        sounds_config = config.get('sounds', {})
        if sounds_config.get('enabled', True) and _sound_player:
            _sound_player.volume = sounds_config.get('volume', 0.7)
            _sound_player.play('sounds/trigger.wav')
        _trigger_haptic(config, 'show_answer')
        return

    if not result:
        return

    sounds_config = config.get('sounds', {})
    if sounds_config.get('enabled', True) and _sound_player:
        sound_path = sounds_config.get('profiles', {}).get(action_name)
        if sound_path:
            _sound_player.volume = sounds_config.get('volume', 0.7)
            _sound_player.play(sound_path)

    _trigger_haptic(config, action_name)
    _process_combo(config, action_name)


COMBO_HAPTIC_PATTERNS = {
    'tier_1': [
        {'type': 'transient', 'time': 0.0, 'intensity': 0.8, 'sharpness': 0.5},
        {'type': 'transient', 'time': 0.08, 'intensity': 1.0, 'sharpness': 0.6},
    ],
    'tier_2': [
        {'type': 'transient', 'time': 0.0, 'intensity': 0.7, 'sharpness': 0.4},
        {'type': 'transient', 'time': 0.07, 'intensity': 0.9, 'sharpness': 0.6},
        {'type': 'transient', 'time': 0.14, 'intensity': 1.0, 'sharpness': 0.8},
    ],
    'tier_3': [
        {'type': 'continuous', 'time': 0.0, 'duration': 0.1, 'intensity': 0.5, 'sharpness': 0.3},
        {'type': 'continuous', 'time': 0.12, 'duration': 0.12, 'intensity': 0.7, 'sharpness': 0.5},
        {'type': 'continuous', 'time': 0.26, 'duration': 0.15, 'intensity': 1.0, 'sharpness': 0.8},
    ],
    'combo_break': [
        {'type': 'continuous', 'time': 0.0, 'duration': 0.15, 'intensity': 1.0, 'sharpness': 1.0},
        {'type': 'continuous', 'time': 0.22, 'duration': 0.3, 'intensity': 0.9, 'sharpness': 0.8},
    ],
    'fail': [
        {'type': 'continuous', 'time': 0.0, 'duration': 0.12, 'intensity': 1.0, 'sharpness': 0.9},
    ],
    'milestone': [
        {'type': 'continuous', 'time': 0.0, 'duration': 0.1, 'intensity': 0.4, 'sharpness': 0.3},
        {'type': 'continuous', 'time': 0.15, 'duration': 0.15, 'intensity': 0.7, 'sharpness': 0.5},
        {'type': 'continuous', 'time': 0.35, 'duration': 0.2, 'intensity': 1.0, 'sharpness': 0.7},
    ],
}


def _process_combo(config, action_name):
    if not _combo_tracker or not _combo_tracker.enabled:
        return

    combo_result = _combo_tracker.feed(action_name)
    if not combo_result:
        return

    event = combo_result.get('event')
    haptics_config = config.get('haptics', {})
    haptics_on = haptics_config.get('enabled', True) and _haptic_player and _haptic_player.is_supported

    if haptics_on:
        _haptic_player.intensity_scale = haptics_config.get('intensity_scale', 1.0)

    if event == 'fail':
        if _visual_effects:
            _visual_effects.show_fail()
        if haptics_on:
            _haptic_player.play_pattern(COMBO_HAPTIC_PATTERNS['fail'])
        return

    if event == 'combo_break':
        lost = combo_result.get('lost_streak', 0)
        if _visual_effects:
            _visual_effects.show_combo_break(lost)
        if haptics_on:
            _haptic_player.play_pattern(COMBO_HAPTIC_PATTERNS['combo_break'])
        return

    if event == 'answer':
        streak = combo_result.get('streak', 0)
        tier = combo_result.get('tier', 0)

        if streak >= 2 and _visual_effects:
            _visual_effects.show_combo(streak, tier)

        if combo_result.get('threshold_hit') and _visual_effects:
            _visual_effects.show_tier_up(tier, streak)

        if tier >= 1 and haptics_on:
            pattern_key = f'tier_{tier}'
            pattern = COMBO_HAPTIC_PATTERNS.get(pattern_key)
            if pattern:
                _haptic_player.play_pattern(pattern)

        milestone = combo_result.get('milestone')
        if milestone:
            if _visual_effects:
                _visual_effects.show_milestone(milestone)
            if haptics_on:
                _haptic_player.play_pattern(COMBO_HAPTIC_PATTERNS['milestone'])


def _trigger_haptic(config, action_name):
    if not _haptic_player or not _haptic_player.is_supported:
        return
    haptics_config = config.get('haptics', {})
    if not haptics_config.get('enabled', True):
        return
    _haptic_player.intensity_scale = haptics_config.get('intensity_scale', 1.0)
    profile = haptics_config.get('profiles', DEFAULT_PROFILES).get(action_name)
    if profile:
        _haptic_player.play(profile)


def start_polling():
    global _poll_timer
    if _poll_timer:
        return
    config = get_config()
    interval = config.get('poll_interval_ms', 16)
    _poll_timer = QTimer()
    _poll_timer.timeout.connect(lambda: _xbox.poll() if _xbox else None)
    _poll_timer.start(interval)
    logger.info('Controller polling started at %dms interval', interval)


def stop_polling():
    global _poll_timer
    if _poll_timer:
        _poll_timer.stop()
        _poll_timer = None


def open_config_dialog():
    from .config_dialog import ConfigDialog
    config = get_config()
    dlg = ConfigDialog(config, sound_player=_sound_player, haptic_player=_haptic_player, parent=mw)
    if dlg.exec():
        get_config()
        tooltip('Xbox Controller 配置已保存', parent=mw)


def setup():
    global _xbox, _sound_player, _haptic_player, _combo_tracker, _visual_effects

    get_config()

    _haptic_player = HapticPlayer()
    haptics_config = (_config or {}).get('haptics', {})
    _haptic_player.enabled = haptics_config.get('enabled', True)
    _haptic_player.intensity_scale = haptics_config.get('intensity_scale', 1.0)

    combo_config = (_config or {}).get('combo', {})
    _combo_tracker = ComboTracker()
    _combo_tracker.enabled = combo_config.get('enabled', True)
    _combo_tracker.milestone_interval = combo_config.get('milestone_interval', 25)
    _combo_tracker.streak_thresholds = combo_config.get('streak_thresholds', [5, 10, 20])

    _visual_effects = VisualEffects(mw)
    _visual_effects.enabled = combo_config.get('visual_effects', True)

    _xbox = XboxController(
        on_button_press=on_button_press,
        on_connect=on_controller_connect,
        on_disconnect=on_controller_disconnect,
    )
    _sound_player = SoundPlayer()

    if _xbox.is_available:
        _xbox.start()
        logger.info('Xbox controller module initialized')
    else:
        logger.info('Xbox controller: GameController framework not available')

    sounds_config = (_config or {}).get('sounds', {})
    _sound_player.enabled = sounds_config.get('enabled', True)
    _sound_player.volume = sounds_config.get('volume', 0.7)

    start_polling()

    action = QAction('Xbox Controller Settings', mw)
    action.triggered.connect(open_config_dialog)
    mw.form.menuTools.addAction(action)

    logger.info('Xbox Controller add-on loaded')


gui_hooks.main_window_did_init.append(setup)
