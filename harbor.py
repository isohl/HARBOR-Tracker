from collections import defaultdict
from BaseHTTPServer import HTTPServer
from zipfile import ZipFile
from shutil import copyfileobj
from SimpleHTTPServer import SimpleHTTPRequestHandler
from threading import Thread, Lock
import cgi, os, time, json, pickle
import sys, math

import fap
import decodeTNC
import D710
import replay
import helper


class TrackNotFoundError(Exception):
    pass


class HARBORHTTPServer(HTTPServer):
    def __init__(self, harbor):
        HTTPServer.__init__(self, ('', 80), HARBORHandler)
        self.harbor = harbor


class HARBORHandler(SimpleHTTPRequestHandler):
    def send_file(self, filename):
        try:
            self.send_response(200, "OKAY")
            self.end_headers()
            copyfileobj(open(filename, 'r'), self.wfile)
        except Exception, e:
            print e
            self.wfile.write("Server error")

    def send_json(self, data):
        try:
            self.send_response(200, "OKAY")
            self.end_headers()
            self.wfile.write(json.dumps(data) + "\n")
        except Exception, e:
            print e
            self.wfile.write("Server error")

    def get_paths(self, requests):
        if len(requests) == 1:
            self.send_json(self.harbor.paths)
        else:
            paths = {}
            for r in requests:
                if r.startswith("callsign="):
                    callsign = r.replace("callsign=","")
                    paths[callsign] = self.harbor.get_path(callsign)
            self.send_json(paths)

    def get_readouts(self, requests):
        if len(requests) == 1:
            readouts = {"tracked" : self.habor.get_readouts()}
            self.send_json(readouts)
        else:
            readouts = {}
            for r in requests:
                if r.startswith("callsign="):
                    callsign = r.replace("callsign=","")
                    readouts[callsign] = self.harbor.get_readouts(callsign)
            self.send_json(readouts)

    def get_ascent_audio(self, requests):
        if len(requests) == 2 and requests[1].startswith("callsign="):
            callsign = r.replace("callsign=","")
            ascent_rate = self.harbor.get_ascent(callsign)
        else:
            ascent_rate = self.harbor.get_ascent()
        filename = "./audio/asc" + str(abs(int(ascent_rate / 100))) + ".mp3"
        self.send_file(filename)
            


    def get_altitude_audio(self, requests):
        if len(requests) == 2 and requests[1].startswith("callsign="):
            callsign = r.replace("callsign=","")
            altitude = self.harbor.get_altitude(callsign)
        else:
            altitude = self.harbor.get_altitude()
        filename = "./audio/alt" + str(int(altitude / 1000)) + ".mp3"
        self.send_file(filename)

    def get_gmaps(self, requests):
        try:
            image = self.harbor.gmaps.open(self.path[1:], 'r')
            self.send_response(200, "OKAY")
            self.end_headers()
            copyfileobj(image, self.wfile)
        except KeyError:
            self.send_response(404, "File Not Found")
            self.end_headers()
            self.wfile.write('Imagery not in cache')

    files = {
        "/" : "web/track.html",
        "/main.js" : "web/main.js",
        "/config" : "web/config.html",
        "/config.js" : "web/config.js",
        "/raw" : "web/raw.html",
        "/raw.js" : "web/raw.js",
        "/jquery.js" : "third_party/jquery.js",
        "/leaflet.js" : "third_party/leaflet.js",
        "/leaflet.css" : "third_party/leaflet.css",
    }

    requests = {
        "/paths" : get_paths,
        "/readouts" : get_readouts,
        "/asc.mp3" : get_ascent_audio,
        "/alt.mp3" : get_altitude_audio,
        "/gmaps" : get_gmaps,
    }

    def do_GET(self):
        if self.path in HARBORHandler.files:
            self.send_file(HARBORHandler.files[self.path])
        elif any(self.path.startswith(endpoint) for endpoint in HARBORHandler.requests):
            requests = self.path.replace('?','&').split("&")
            HARBORHandler.requests[self.path](self, requests)
        else:
            self.send_response(200, "OKAY")
            self.end_headers()
            self.wfile.write("Unknown request")

    def do_POST(self):
        pass

class Harbor(object):
    def __init__(self):
        self.mainlock = Lock()
        try:
            with open('.state', 'rb') as f:
                self.paths = pickle.load(f)
                self.log = defaultdict(defaultStyle)
        except (IOError, EOFError):
            with self.mainlock:
                self._initialize_defaults()
        self.gmaps = ZipFile("gmaps.zip", "r")

    def _initialize_defaults(self):
        self.paths = defaultdict(list)
        self.tracked = ["WB1SAR-11","KF7WII-11"]
        self.save_state()

    def _get_last_points(callsign):
        if callsign is None:
            last_points = []
            for callsign in self.tracked:
                path = self.paths[callsign]
                if len(path) > 0:
                    last_points.append(path[-1])
                    if len(path) > 1:
                        last_points.append(path[-2])
            track = last_points.sort(key=lambda x: x.time) 
        else:
            track = self.paths[callsign]
        if len(track) < 2:
            return None, None
        point = track[-1]
        point_before = track[-2]
        return point, point_before

    def get_ascent(self, callsign=None):
        point, point_before = self._get_last_points(callsign)
        if point is None:
            return 0
        return int((float(point.altitude) - float(point_before.altitude)) /
                 (float(point_before.time - point.time) / 60) / 100) * 100

    def get_altitude(self, callsign=None):
        point, point_before = self._get_last_points(callsign)
        if point is None:
            return 0
        return point.altitude

    def get_readouts(self, callsign=None, VOR = (40.1490956, -110.1270281)):
        point, point_before = self._get_last_points(callsign)
        readouts = {"ascent":0,"altitude":0,"bearing":0,"range":0}
        if point is None:
            return readouts
        readouts["ascent"] = self.get_ascent(callsign)
        readouts["altitude"] = point.altitude
        x_dist = helper.miles_to_longitude(point.longitude - VOR[1], point.latitude)
        y_dist = helper.miles_to_latitude(point.latitude - VOR[0])
        readouts["bearing"] = int(450 - math.degrees(math.atan2(y_dist,x_dist))) % 360
        readouts["range"] = int(math.hypot(x_dist, y_dist) * 10) / 10
        return readouts


    def save_state(self):
        with self.mainlock:
            dat = self.paths
        with open('state.sheyne', 'wb') as f:
            pickle.dump(dat, f, 2)


    def add_point(self, track, point):
        with self.mainlock:
            self.paths[track].append(point)
        self.save_state()


    def get_path(self, callsign):
        with self.mainlock:
            if callsign in self.paths:
                return self.paths[callsign]


    def submit_packet(self, packet):
        try: # Pass the packet to FAP for parsing (accepts MicE, but not D710)
            p = fap.Packet(packet)
            if p.altitude:
                point = helper.Point(time=time.time(), altitude=int(p.altitude * 3.28084),
                                     latitude=p.latitude, longitude=p.longitude)
                self.add_point(p.src_callsign, point)
        except fap.DecodeError:
            if decodeTNC.determine_compatability(packet):
                latitude, longitude = decodeTNC.latlong(packet)
                point = helper.Point(time=time.time(), altitude=0, latitude=latitude, longitude=longitude)
                self.add_point("D710", point)
        except AttributeError:
            print "Invalid packet: "+str(packet)


if __name__ == "__main__":
    filename = None
    if "-r" in sys.argv:
        filename = sys.argv[sys.argv.index("-r")+1]

    print "Starting HARBOR tracker"
    h = Harbor()

    if filename:
        print "Beginning replay of: " + str(filename)
        player = Thread(target=lambda: replay.Replay(filename,h))
        player.start()
    else:
        comport = None
        print "Starting D710 interface"
        if os.name == "nt":
            comport = raw_input("What is the name of the COM Port? (COM1, etc) ")

        t = Thread(target=lambda: D710.main(h, comport))
        t.start()

    print "Starting web server"
    httpd = HARBORHTTPServer(h)
    httpd.serve_forever()
