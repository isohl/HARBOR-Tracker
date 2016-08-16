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


def cleanup(x):
    return x.replace('_SPACE_', ' ')


def defaultStyle():
    return {'color': '#00f'}


class TrackNotFoundError(Exception):
    pass


class HARBORHTTPServer(HTTPServer):
    def __init__(self, harbor):
        HTTPServer.__init__(self, ('', 80), HARBORHandler)
        self.harbor = harbor


class HARBORHandler(SimpleHTTPRequestHandler):

    def out_tracks(self):
        self.send_response(200, "OKAY")
        self.end_headers()
        self.json_out(self.server.harbor.getTracks())

    def out_meta(self):
        self.send_response(200, "OKAY")
        self.end_headers()
        self.json_out(self.server.harbor.trackMeta)

    def out_log(self):
        self.send_response(200, "OKAY")
        self.end_headers()
        self.json_out(self.server.harbor.log)

    def json_out(self, obj):
        self.wfile.write(json.dumps(obj) + "\n")

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type'],}
        )
        try:
            name = form['name'].value
        except KeyError:
            name = self.path[1:]
        for field in form:
            if field != 'name':
                self.server.harbor.setParam(name, field, form[field].value)
        self.out_meta()

    def do_GET(self):
        ADDPOINT = '/addpoint/'
        ADDCALLSIGN = '/addcallsign/'
        REMOVECALLSIGN = '/removecallsign/'
        GMAPS = '/gmaps/'
        STATICS = ('/audio', '/leaflet', '/jquery', '/web',
                   '/scripts')
        if self.path == "/trackdata":
            self.send_response(200, "OKAY")
            self.end_headers()
            self.json_out(self.server.harbor.trackPoints)
        elif self.path.startswith(GMAPS):
            try:
                image = self.server.harbor.gmaps.open(self.path[1:], 'r')
                self.send_response(200, "OKAY")
                self.end_headers()
                copyfileobj(image, self.wfile)
            except KeyError:
                self.send_response(404, "File Not Found")
                self.end_headers()
                self.wfile.write('We dont have that image: infinite sadness')
        elif self.path == "/tracks":
            self.out_tracks()
        elif self.path == "/log":
            self.out_log()
        elif self.path == "/reset":
            self.server.harbor.initialize()
        elif self.path == "/clearpaths":
            self.server.harbor.resetPaths()
        elif self.path == "/meta":
            self.out_meta()
        elif self.path == "/info":
            self.send_response(200, "OKAY")
            self.end_headers()
            self.json_out(self.server.harbor.getInfo())
        elif self.path == "/asc.mp3":
            self.send_response(200, "OKAY")
            self.end_headers()
            audio = open("./audio/asc" + str(abs(int(self.server.harbor.readouts["ascent"] / 100))) + ".mp3", 'rb')
            copyfileobj(audio, self.wfile)
        elif self.path == "/alt.mp3":
            self.send_response(200, "OKAY")
            self.end_headers()
            audio = open("./audio/alt" + str(int(self.server.harbor.readouts["altitude"] / 1000)) + ".mp3", 'rb')
            copyfileobj(audio, self.wfile)
        elif self.path == "/":
            self.send_response(200, "OKAY")
            self.end_headers()
            copyfileobj(open('web/track.html', 'r'), self.wfile)
        elif self.path == "/config":
            self.send_response(200, "OKAY")
            self.end_headers()
            copyfileobj(open('web/config.html', 'r'), self.wfile)
        elif self.path == "/active":
            self.send_response(200, "OKAY")
            self.end_headers()
            copyfileobj(open('web/active.html', 'r'), self.wfile)
        elif self.path.startswith(ADDCALLSIGN):
            callsign, track = self.path[len(ADDCALLSIGN):].split('/')
            self.server.harbor.addCallsign(cleanup(callsign), cleanup(track))
            self.out_tracks()
        elif self.path.startswith(REMOVECALLSIGN):
            callsign, track = self.path[len(REMOVECALLSIGN):].split('/')
            self.server.harbor.removeCallsign(cleanup(callsign), cleanup(track))
            self.out_tracks()

        elif self.path.startswith(ADDPOINT):
            track, point = self.path[len(ADDPOINT):].split('/')
            point = point.split(',')
            point = tuple(float(part) for part in point)
            self.server.harbor.add_point(track, helper.Point(*point))
        elif reduce(lambda a, b: a or b, (self.path.startswith(k) for k in STATICS)):
            # if the path starts with any of the statics, run it through
            # SimpleHTTPRequestHandler. This effictively serves it statically.
            SimpleHTTPRequestHandler.do_GET(self)
        else:
            # for now this is nicer than an HTTP error.
            self.send_response(200, "OKAY")
            self.end_headers()
            self.wfile.write('Missing Request' + "\n")

class Harbor(object):
    def __init__(self):
        self.mainlock = Lock()
        try:
            with open('.state', 'rb') as f:
                self.paths = pickle.load(f)
                self.log = defaultdict(defaultStyle)
        except (IOError, EOFError):
            with self.mainlock:
                self.paths = defaultdict(list)
                self.save_state()
        self.gmaps = ZipFile("gmaps.zip", "r")

    def get_readouts(self, callsign, VOR = (40.1490956, -110.1270281)):
        track = self.paths[callsign]
        if len(track) < 2:
            return None
        point = track[-1]
        point_before = track[-2]
        readouts = {}
        readouts["ascent"] = int((float(point.altitude) - float(point_before.altitude)) /
                 (float(point_before.time - point.time) / 60) / 100) * 100
        readouts["altitude"] = point.altitude
        readouts["last_packet"] = point.time
        x_dist = helper.miles_to_longitude(point.longitude - VOR[1], point.latitude)
        y_dist = helper.miles_to_latitude(point.latitude - VOR[0])
        readouts["bearing"] = int(450 - math.degrees(math.atan2(y_dist,x_dist))) % 360
        readouts["range"] = int(math.hypot(x_dist, y_dist) * 10) / 10


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

    h = Harbor()

    if filename:
        player = Thread(target=lambda: replay.Replay(filename,h))
        player.start()
    else:
        comport = None
        if os.name == "nt":
            comport = raw_input("What is the name of the COM Port? (COM1, etc) ")

        t = Thread(target=lambda: D710.main(h, comport))
        t.start()

    httpd = HARBORHTTPServer(h)
    httpd.serve_forever()
