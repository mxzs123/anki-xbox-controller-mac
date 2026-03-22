import logging
import os
import platform
import subprocess
import threading

logger = logging.getLogger(__name__)

_addon_dir = os.path.dirname(os.path.abspath(__file__))


class SoundPlayer:
    def __init__(self):
        self._volume = 0.7
        self._enabled = True

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = bool(value)

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = max(0.0, min(1.0, float(value)))

    def play(self, sound_path):
        if not self._enabled:
            return

        if not os.path.isabs(sound_path):
            sound_path = os.path.join(_addon_dir, sound_path)

        if not os.path.isfile(sound_path):
            logger.debug('Sound file not found: %s', sound_path)
            return

        threading.Thread(target=self._play_async, args=(sound_path,), daemon=True).start()

    def _play_async(self, path):
        try:
            if platform.system() == 'Darwin':
                vol = int(self._volume * 100)
                subprocess.run(
                    ['afplay', '-v', str(self._volume), path],
                    capture_output=True,
                    timeout=5,
                )
            else:
                logger.debug('Sound playback not supported on this platform')
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            logger.debug('Sound playback failed: %s', e)
