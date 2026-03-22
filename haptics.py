import logging
import platform

logger = logging.getLogger(__name__)

_ch_available = False

if platform.system() == 'Darwin':
    try:
        from CoreHaptics import (
            CHHapticPattern,
            CHHapticEvent,
            CHHapticEventParameter,
            CHHapticEventParameterIDHapticIntensity,
            CHHapticEventParameterIDHapticSharpness,
            CHHapticEventTypeHapticTransient,
            CHHapticEventTypeHapticContinuous,
        )
        _ch_available = True
    except ImportError:
        logger.warning('CoreHaptics framework not available')
    except Exception as e:
        logger.warning('CoreHaptics load failed: %s', e)

DEFAULT_PROFILES = {
    'answer_1': {'type': 'continuous', 'intensity': 1.0, 'sharpness': 0.8, 'duration': 0.5},
    'answer_2': {'type': 'continuous', 'intensity': 0.9, 'sharpness': 0.6, 'duration': 0.3},
    'answer_3': {'type': 'continuous', 'intensity': 0.8, 'sharpness': 0.5, 'duration': 0.25},
    'answer_4': {'type': 'continuous', 'intensity': 0.7, 'sharpness': 0.4, 'duration': 0.2},
    'show_answer': {'type': 'continuous', 'intensity': 1.0, 'sharpness': 0.7, 'duration': 0.35},
    'replay_audio': {'type': 'continuous', 'intensity': 0.6, 'sharpness': 0.5, 'duration': 0.2},
    'undo': {'type': 'continuous', 'intensity': 0.8, 'sharpness': 0.6, 'duration': 0.3},
}


class HapticPlayer:
    def __init__(self):
        self._engine = None
        self._supported = False
        self.enabled = True
        self.intensity_scale = 1.0

    @property
    def is_supported(self):
        return self._supported

    def attach(self, gc_controller):
        if not _ch_available or gc_controller is None:
            self._supported = False
            return

        try:
            haptics = gc_controller.haptics()
            if haptics is None:
                logger.info('Controller does not support haptics')
                self._supported = False
                return

            engine = haptics.createEngineWithLocality_('Default')
            if engine is None:
                logger.info('Failed to create haptic engine')
                self._supported = False
                return

            result = engine.startAndReturnError_(None)
            success = result[0] if isinstance(result, tuple) else result
            error = result[1] if isinstance(result, tuple) else None
            if not success:
                logger.warning('Haptic engine start failed: %s', error)
                self._supported = False
                return

            self._engine = engine
            self._supported = True
            logger.info('Haptic engine started')
        except Exception as e:
            logger.warning('Haptics init failed: %s', e)
            self._supported = False

    def detach(self):
        if self._engine:
            try:
                self._engine.stopWithCompletionHandler_(None)
            except Exception as e:
                logger.debug('Haptic engine stop error: %s', e)
        self._engine = None
        self._supported = False

    def play(self, profile):
        if not self.enabled or not self._supported or not self._engine:
            return

        if not _ch_available:
            return

        try:
            event_type = profile.get('type', 'transient')
            intensity = min(1.0, profile.get('intensity', 0.5) * self.intensity_scale)
            sharpness = profile.get('sharpness', 0.3)
            duration = profile.get('duration', 0.1)

            params = [
                CHHapticEventParameter.alloc().initWithParameterID_value_(
                    CHHapticEventParameterIDHapticIntensity, intensity
                ),
                CHHapticEventParameter.alloc().initWithParameterID_value_(
                    CHHapticEventParameterIDHapticSharpness, sharpness
                ),
            ]

            if event_type == 'continuous':
                haptic_type = CHHapticEventTypeHapticContinuous
            else:
                haptic_type = CHHapticEventTypeHapticTransient
                duration = 0

            event = CHHapticEvent.alloc().initWithEventType_parameters_relativeTime_duration_(
                haptic_type, params, 0, duration
            )

            result = CHHapticPattern.alloc().initWithEvents_parameters_error_(
                [event], [], None
            )
            pattern = result[0] if isinstance(result, tuple) else result
            if pattern is None:
                logger.debug('Failed to create haptic pattern: %s', result)
                return

            result = self._engine.createPlayerWithPattern_error_(pattern, None)
            player = result[0] if isinstance(result, tuple) else result
            if player is None:
                logger.debug('Failed to create haptic player: %s', result)
                return

            result = player.startAtTime_error_(0, None)
            success = result[0] if isinstance(result, tuple) else result
            if not success:
                logger.debug('Haptic play failed: %s', result)
        except Exception as e:
            logger.debug('Haptic play error: %s', e)

    def play_pattern(self, events_data):
        if not self.enabled or not self._supported or not self._engine or not _ch_available:
            return

        try:
            events = []
            for ev in events_data:
                intensity = min(1.0, ev.get('intensity', 0.5) * self.intensity_scale)
                sharpness = ev.get('sharpness', 0.3)
                duration = ev.get('duration', 0.1)
                rel_time = ev.get('time', 0.0)
                ev_type = ev.get('type', 'transient')

                params = [
                    CHHapticEventParameter.alloc().initWithParameterID_value_(
                        CHHapticEventParameterIDHapticIntensity, intensity
                    ),
                    CHHapticEventParameter.alloc().initWithParameterID_value_(
                        CHHapticEventParameterIDHapticSharpness, sharpness
                    ),
                ]

                if ev_type == 'continuous':
                    haptic_type = CHHapticEventTypeHapticContinuous
                else:
                    haptic_type = CHHapticEventTypeHapticTransient
                    duration = 0

                event = CHHapticEvent.alloc().initWithEventType_parameters_relativeTime_duration_(
                    haptic_type, params, rel_time, duration
                )
                events.append(event)

            result = CHHapticPattern.alloc().initWithEvents_parameters_error_(
                events, [], None
            )
            pattern = result[0] if isinstance(result, tuple) else result
            if pattern is None:
                logger.debug('Failed to create haptic pattern: %s', result)
                return

            result = self._engine.createPlayerWithPattern_error_(pattern, None)
            player = result[0] if isinstance(result, tuple) else result
            if player is None:
                logger.debug('Failed to create haptic player: %s', result)
                return

            result = player.startAtTime_error_(0, None)
            success = result[0] if isinstance(result, tuple) else result
            if not success:
                logger.debug('Haptic pattern play failed: %s', result)
        except Exception as e:
            logger.debug('Haptic pattern play error: %s', e)

    def play_test(self):
        self.play({'type': 'continuous', 'intensity': 1.0, 'sharpness': 0.5, 'duration': 0.3})
