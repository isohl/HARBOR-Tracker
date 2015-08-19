from collections import defaultdict
from BaseHTTPServer import HTTPServer
from helper import *
from zipfile import ZipFile
from shutil import copyfileobj
from SimpleHTTPServer import SimpleHTTPRequestHandler 
from threading import Thread, Lock
from random import randint
import cgi
import time
import json
import pickle
import math

def cleanup(x):
	return x.replace('_SPACE_', ' ')

def handler(harbor):
	class Handler(SimpleHTTPRequestHandler):
		def out_tracks(self):
			self.send_response(200, "OKAY")
			self.end_headers()
			self.json_out(self.harbor.getTracks())
		def out_meta(self):
			self.send_response(200, "OKAY")
			self.end_headers()
			self.json_out(self.harbor.trackMeta)
		def out_log(self):
			self.send_response(200, "OKAY")
			self.end_headers()
			self.json_out(self.harbor.log)
		def json_out(self, obj):
			self.wfile.write(json.dumps(obj)+"\n")
		def do_POST(self):
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
					'CONTENT_TYPE':self.headers['Content-Type'],}
				)
			try:
				name = form['name'].value
			except KeyError:
				name = self.path[1:]			
			for field in form:
				if field != 'name':
					self.harbor.setParam(name, field, form[field].value)
			self.out_meta()
		def do_GET(self):
			ADDPOINT = '/addpoint/'
			ADDCALLSIGN = '/addcallsign/'
			REMOVECALLSIGN = '/removecallsign/'
			GMAPS = '/gmaps/'
			STATICS = ('/audio','/leaflet','/jquery', '/scripts')
			if self.path == "/trackdata":
				self.send_response(200, "OKAY")
				self.end_headers()
				self.json_out(self.harbor.trackPoints)
			elif self.path.startswith(GMAPS):
				try:
					image = self.harbor.gmaps.open(self.path[1:], 'r')
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
				self.harbor.init()
			elif self.path == "/clearpaths":
				self.harbor.resetPaths()
			elif self.path == "/meta":
				self.out_meta()
			elif self.path == "/info":
				self.send_response(200, "OKAY")
				self.end_headers()
				self.json_out(self.harbor.getInfo())
			elif self.path == "/asc.mp3":
				self.send_response(200, "OKAY")
				self.end_headers()
				audio = open("./audio/asc"+str(abs(int(self.harbor.readouts["ascent"]/100)))+".mp3",'rb')
				copyfileobj(audio,self.wfile)
			elif self.path == "/alt.mp3":
				self.send_response(200, "OKAY")
				self.end_headers()
				audio = open("./audio/alt"+str(int(self.harbor.readouts["altitude"]/1000))+".mp3",'rb')
				copyfileobj(audio,self.wfile)
			elif self.path == "/":
				self.send_response(200, "OKAY")
				self.end_headers()
				copyfileobj(open('track.html', 'r'),self.wfile)
			elif self.path == "/config":
				self.send_response(200, "OKAY")
				self.end_headers()
				copyfileobj(open('config.html', 'r'),self.wfile)
			elif self.path == "/active":
				self.send_response(200, "OKAY")
				self.end_headers()
				copyfileobj(open('active.html', 'r'),self.wfile)
			elif self.path.startswith(ADDCALLSIGN):
				callsign, track = self.path[len(ADDCALLSIGN):].split('/')
				self.harbor.addCallsign(cleanup(callsign), cleanup(track))
				self.out_tracks()
			elif self.path.startswith(REMOVECALLSIGN):
				callsign, track = self.path[len(REMOVECALLSIGN):].split('/')
				self.harbor.removeCallsign(cleanup(callsign), cleanup(track))
				self.out_tracks()

			elif self.path.startswith(ADDPOINT):
				track, point = self.path[len(ADDPOINT):].split('/')
				point = point.split(',')
				point = tuple(float(part) for part in point)
				self.harbor.addPoint(track,Point(*point))
			elif reduce(lambda a, b: a or b, (self.path.startswith(k) for k in STATICS)):
				# if the path starts with any of the statics, run it through 
				# SimpleHTTPRequestHandler. This effictively serves it statically. 
				SimpleHTTPRequestHandler.do_GET(self)
			else:
				# for now this is nicer than an HTTP error. 
				self.send_response(200, "OKAY")
				self.end_headers()
				self.wfile.write('hmm'+"\n")
	Handler.harbor = harbor
	return Handler
def defaultStyle():
	return {'color':'#00f'}

class TrackNotFoundError(Exception): pass
class Harbor():
	def __init__(self, state=False):
		doInit = True
		if state:
			doInit = False
			try:
				with open('state.sheyne', 'rb') as f:
					self.trackPoints, self.trackNames, self.trackMeta, self.readouts, self.id = pickle.load(f)
					self.log = defaultdict(defaultStyle)
			except (IOError,EOFError):
				doInit = True
		if doInit:
			self.init()
		self.gmaps = ZipFile("gmaps.zip", "r")
	
	def init(self):
		with mainLock:
			self.resetId()
			self.trackPoints = defaultdict(list)
			self.trackNames = defaultdict(set)
			self.log = defaultdict(defaultStyle)
			self.trackMeta = defaultdict(defaultStyle)
			self.readouts = {'bearing': 0, 'range': 0, 'ascent': 0, 'altitude': 0, 'primary':"Balloon", 'last_packet':time.time()}
			self.saveState()
	
	def resetId(self):
		self.id = time.time()

	def resetPaths(self):
		with mainLock:
			self.resetId()
			self.trackPoints = defaultdict(list)
			self.saveState()

	def saveState(self):
		dat = (self.trackPoints, self.trackNames, self.trackMeta, self.readouts, self.id)
		with open('state.sheyne', 'wb') as f:
			pickle.dump(dat, f, 2)

	def setParam(self, track, attribute, value):
		self.resetId()
		self.trackMeta[cleanup(track)][attribute] = value
		self.saveState()

	
	def addPoint(self, track, point):
		self.trackPoints[track].append(point)
		if self.readouts["primary"] == track:
			self.readouts["ascent"] = int(float(point.altitude - float(self.readouts["altitude"])) / ((float(time.time()) - float(self.readouts["last_packet"])) / 60) / 100) * 100
			self.readouts["altitude"] = point.altitude
			self.readouts["last_packet"] = time.time()
			x_dist = mile_change_longitude(float(point.latitude),float(point.longitude)-(-110.1270281))
			y_dist = mile_change_latitude(float(point.latitude)-40.1490956)
			#Myton VOR: 40.1490956, -110.1270281
			bearing = math.degrees(math.atan2(-y_dist,x_dist)) + 90 # -180 to 180 with 0 at north
			if bearing < 0:
				bearing += 360
			self.readouts["bearing"] = int(bearing) # 0 to 360 east of north
			self.readouts["range"] = int(math.hypot(x_dist,y_dist)*10)/10
		self.saveState()
	
	def addCallsign(self, callsign, track):
		self.trackMeta[track]
		self.trackNames[track].add(callsign)
		self.saveState()
	
	def removeCallsign(self, callsign, track):
		self.trackNames[track].remove(callsign)
		self.saveState()
	
	def getTrack(self, callsign):
		for track, names in self.trackNames.items():
			if callsign in names:
				return track
		raise TrackNotFoundError()
	def getTracks(self):
		return {key: list(v) for key,v in self.trackNames.items()}
	def newPoint(self, callsign, point):
		try:
			self.log[callsign] = point.time
			self.addPoint(self.getTrack(callsign), point)
		except TrackNotFoundError:
			pass
	def getInfo(self):
		return {'id':self.id,'tracks':self.getTracks(), 'readouts':self.readouts, 'trackdata': self.trackPoints, 'trackmeta':self.trackMeta}

mainLock = Lock()
h = Harbor(state=True)

import D710
dontDie = True
def src():
	while dontDie:
		with mainLock:
			if len(h.trackPoints['Car 1']) > 0:
				last_point = h.trackPoints['Balloon'][-1]
				last_d710_point = h.trackPoints['Car 1'][-1]
			else:
				h.addCallsign("WB1SAR-11", "Balloon")
				h.addCallsign("KF7WII-11", "Balloon")
				h.addCallsign("KE7ROS-11", "Balloon")
				h.addCallsign("D710", "Car 1")
				last_d710_point = Point(time.time(),40.191484, -110.385534,1000)
				h.newPoint("D710", last_d710_point)
				last_point = Point(time.time(),40.191584, -110.385634, 1000)
				h.newPoint("WB1SAR-11", last_point)

			h.readouts['ascent'] += randint(-10, 10)
			last_point = Point(time.time(), last_point.latitude + float(randint(-2, 4))/1000, last_point.longitude + float(randint(-2, 6))/1000,1000)
			h.newPoint("WB1SAR-11", last_point)
			last_d710_point = Point(time.time(), last_d710_point.latitude + float(randint(-2, 4))/1000, last_d710_point.longitude + float(randint(-2, 6))/1000,1000)
			h.newPoint("D710", last_d710_point)
		time.sleep(3)

import os
comport = None
if os.name=="nt":
	comport = raw_input("What is the name of the COM Port? (COM1, etc) ")

def callIan():
	D710.main(h,comport)
t = Thread(target=callIan)
t.daemon = True
t.start()

server_address = ('', 8001)
httpd = HTTPServer(server_address, handler(h))
httpd.serve_forever()

dontDie = False