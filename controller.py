import logging
import platform

logger = logging.getLogger(__name__)

_gc_available = False
_ns_available = False

if platform.system() == 'Darwin':
    try:
        import objc
        from GameController import (
            GCController,
            GCControllerDidConnectNotification,
            GCControllerDidDisconnectNotification,
        )
        _gc_available = True
    except ImportError:
        logger.warning('pyobjc-framework-GameController not found; controller input disabled')
    except Exception as e:
        logger.warning('GameController framework load failed: %s', e)

    try:
        from Foundation import NSNotificationCenter
        _ns_available = True
    except ImportError:
        logger.warning('Foundation framework not available')
    except Exception as e:
        logger.warning('Foundation framework load failed: %s', e)

BUTTON_NAMES = ['A', 'B', 'X', 'Y']
TRIGGER_NAMES = ['left_trigger', 'right_trigger']
ALL_INPUT_NAMES = BUTTON_NAMES + TRIGGER_NAMES

TRIGGER_THRESHOLD = 0.5


class XboxController:
    def __init__(self, on_button_press=None, on_connect=None, on_disconnect=None):
        self._controller = None
        self._on_button_press = on_button_press
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._prev_button_state = {}
        self._connected = False
        self._observers = []

    @property
    def is_available(self):
        return _gc_available

    @property
    def is_connected(self):
        return self._connected and self._controller is not None

    @property
    def controller_name(self):
        if self._controller:
            try:
                return str(self._controller.vendorName() or 'Unknown')
            except Exception:
                pass
        return 'Not Connected'

    def start(self):
        if not _gc_available or not _ns_available:
            logger.info('GameController or Foundation framework not available')
            return False

        from Foundation import NSNotificationCenter
        nc = NSNotificationCenter.defaultCenter()

        obs1 = nc.addObserverForName_object_queue_usingBlock_(
            GCControllerDidConnectNotification,
            None,
            None,
            lambda note: self._handle_connect(note.object()),
        )
        obs2 = nc.addObserverForName_object_queue_usingBlock_(
            GCControllerDidDisconnectNotification,
            None,
            None,
            lambda note: self._handle_disconnect(note.object()),
        )
        self._observers = [obs1, obs2]

        controllers = GCController.controllers()
        if controllers and len(controllers) > 0:
            self._handle_connect(controllers[0])

        logger.info('Xbox controller listener started')
        return True

    def stop(self):
        if self._observers and _ns_available:
            from Foundation import NSNotificationCenter
            nc = NSNotificationCenter.defaultCenter()
            for obs in self._observers:
                nc.removeObserver_(obs)
        self._observers = []
        self._controller = None
        self._connected = False
        self._prev_button_state = {}
        logger.info('Xbox controller listener stopped')

    def poll(self):
        if not self._connected or not self._controller:
            return

        try:
            gamepad = self._controller.extendedGamepad()
            if not gamepad:
                gamepad = self._controller.gamepad()
            if not gamepad:
                return
        except Exception:
            return

        current_state = {}
        try:
            current_state['A'] = bool(gamepad.buttonA().isPressed())
            current_state['B'] = bool(gamepad.buttonB().isPressed())
            current_state['X'] = bool(gamepad.buttonX().isPressed())
            current_state['Y'] = bool(gamepad.buttonY().isPressed())
        except Exception as e:
            logger.debug('Failed to read face buttons: %s', e)
            return

        try:
            extended = self._controller.extendedGamepad()
            if extended:
                current_state['left_trigger'] = float(extended.leftTrigger().value()) > TRIGGER_THRESHOLD
                current_state['right_trigger'] = float(extended.rightTrigger().value()) > TRIGGER_THRESHOLD
            else:
                current_state['left_trigger'] = False
                current_state['right_trigger'] = False
        except Exception:
            current_state['left_trigger'] = False
            current_state['right_trigger'] = False

        for name in ALL_INPUT_NAMES:
            is_pressed = current_state.get(name, False)
            was_pressed = self._prev_button_state.get(name, False)
            if is_pressed and not was_pressed:
                if self._on_button_press:
                    try:
                        self._on_button_press(name)
                    except Exception as e:
                        logger.error('Button press callback error for %s: %s', name, e)

        self._prev_button_state = current_state

    def _handle_connect(self, gc_controller):
        if gc_controller is None:
            return
        self._controller = gc_controller
        self._connected = True
        self._prev_button_state = {}
        name = 'Unknown'
        try:
            name = str(gc_controller.vendorName() or 'Unknown')
        except Exception:
            pass
        logger.info('Controller connected: %s', name)
        if self._on_connect:
            try:
                self._on_connect(gc_controller)
            except Exception as e:
                logger.error('on_connect callback error: %s', e)

    def _handle_disconnect(self, gc_controller):
        if gc_controller is not None and gc_controller == self._controller:
            self._controller = None
            self._connected = False
            self._prev_button_state = {}
            logger.info('Controller disconnected')
            if self._on_disconnect:
                try:
                    self._on_disconnect(gc_controller)
                except Exception as e:
                    logger.error('on_disconnect callback error: %s', e)
