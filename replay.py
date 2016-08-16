import time
import fap
import helper
import decodeTNC

class Replay(object):
    def __init__(self, filename, harbor):
        self._filename = filename
        self._speed = 1.0
        self._current_time = 0
        self._playing = True
        self._harbor = harbor
        self._main()

    def _main(self):
        with open(self._filename, "r") as fp:
            while 1:
                if self._playing:
                    new_line = fp.readline()
                    if new_line.startswith("# "):
                        timestamp = int(new_line.split(' ')[1])
                        message = fp.readline()
                        if not message:
                            break
                        to_wait = timestamp - self._current_time
                        if to_wait < 0 or self._current_time == 0:
                            to_wait = 0
                        time.sleep(to_wait // self._speed)
                        self._current_time = timestamp
                        print message

                        self._harbor.submit_packet(message)
