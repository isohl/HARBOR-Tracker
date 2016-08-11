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

                        # From D710.py:
                        try:
                            # Pass the packet to FAP for parsing (accepts MicE, but not D710)
                            p = fap.Packet(message)
                            if p.altitude:
                                point = helper.Point(time=timestamp, altitude=int(p.altitude * 3.28084),
                                                     latitude=p.latitude, longitude=p.longitude)
                                self._harbor.newPoint(p.src_callsign, point)
                        except fap.DecodeError:
                            # A Decode Error will occur whenever FAP is unable to parse the packet
                            # In this case, check to see if the packet is a GPRMC or PKWDPOS packet
                            gpscompatible = decodeTNC.determineCompatability(message, ["$PKWDPOS", "$GPRMC"])
                            if gpscompatible:
                                # If it is a D710 packet, parse it.
                                latlong = decodeTNC.latlong(message)  # returned as (latitude,longitude)
                                # If we are plotting D710 tracks, Plot it on Google Earth
                                point = helper.Point(time=timestamp, altitude=0, latitude=latlong[1],
                                                     longitude=latlong[0])
                                self._harbor.newPoint("D710", point)
                            continue
                        except AttributeError:
                            print "Error in packet"
                            continue
