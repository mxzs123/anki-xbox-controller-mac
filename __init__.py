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

_xbox = None
_sound_player = None
_haptic_player = None
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
    global _xbox, _sound_player, _haptic_player

    get_config()

    _haptic_player = HapticPlayer()
    haptics_config = (_config or {}).get('haptics', {})
    _haptic_player.enabled = haptics_config.get('enabled', True)
    _haptic_player.intensity_scale = haptics_config.get('intensity_scale', 1.0)

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
