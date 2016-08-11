import fap
import serial
import datetime
import time
from glob import glob
import os
import decodeTNC
import helper

D710_startup = """
#Don't send CONTROL-C before this line
##META <no-ctrl-c>
TC 1
##Pause for one second
##META <delay>
##META <delay>
##META <no-ctrl-c>
TNC 2
##META <delay>
##META <delay>
##META <no-ctrl-c>
GU 1
##META <delay>
##META <delay>
##META <no-ctrl-c>
TC 0
##META <delay>
##META <delay>
HID off
#CWID off
AWlen 8
BBSMsgs ON
B E 0
LOC E 0
Echo off
FLow off
AUTOLF off
MCOM off
MON ON
MRPt on
PACLen 128
PASSALL off
HBAUD 1200
TXDELAY 25
HEADERLN off
BEACON EVERY 0
GBAUD 4800
GPSTEXT $GPRMC
LTMH OFF
LTM 10
#"""


def run_tnc(ser, lines):
    ctrlC = chr(0x03)
    for line in lines.split("\n"):
        if line[0:2] == "##":
            if line == "##META <delay>":
                print "delaying"
                time.sleep(.5)
            elif line == "##META <no-ctrl-c>":
                print "NO-Ctrl-C"
                ctrlC = ""
        elif line[0:1] == "#":
            print "\t\t", line
        else:
            print "command", line
            ser.write(ctrlC + line + "\r")
            ctrlC = chr(0x03)


def run_d710_tnc_startup(ser):
    run_tnc(ser, D710_startup)


def main(h, com=None):
    while 1:
        if os.name == "nt":  # NT is the special name for Windows
            # The best way to determine what the port is, is to open Device manager and look under COM
            # comport = raw_input("What is the name of the COM Port? (COM1, etc) ")
            comport = com
            try:
                ser = serial.Serial(comport)
            except IndexError:
                print "Serial Device not connected"  # Again, if this isn't working, make sure its plugged in
            try:
                filepath = os.path.join('tnclogs', 'tnc.log')
                log = open(filepath, "a")
            except IOError:  # This will only ever have problems if the folder defined doesn't exist
                os.mkdir('tnclogs')
                log = open(os.path.join('tnclogs', 'tnc.log'), "a")
            log.close()
        else:
            if os.name != "posix":  # Posix is the special name for Unix (Mac)
                print "Unknown operating system"
            try:
                try:
                    ser = serial.Serial(
                        "/dev/tty.usbserial")  # Which of these works will determine on which drivers you have
                except serial.serialutil.SerialException:
                    ser = serial.Serial(glob("/dev/tty.PL2303-*")[0])
            except:
                print "Error Connecting to Device"  # If you get this, either the device is not responding or is not plugged in
                import sys
                sys.exit()
            filepath = "tnclogs/tnc.log"
            log = open(filepath, "a")  # This opens the log, change it to whichever file you like
            log.close()
        # This will run the main startup sequence, which consists of sending a large amount of gibberish to the D710
        run_d710_tnc_startup(ser)

        try:  # This entire try statement is a complicated way of pulling data
            while 1:  # off of the D710 and attaching a time stamp to it in the file
                log = open(filepath, "a")
                got = ser.read()
                out = ""
                while got != "\r":
                    out += got
                    got = ser.read()
                if out != "":
                    currentTimestamp = "# " + str(int(round(time.time()))) + datetime.datetime.now().strftime(
                        " %a %b %d %H:%M:%S %Z %Y")
                    print currentTimestamp
                    print out
                    log.write(currentTimestamp + "\n")
                    log.write(out + "\n")
                    log.flush()
                    log.close()
                    try:
                        # Pass the packet to FAP for parsing (accepts MicE, but not D710)
                        p = fap.Packet(out)
                        if p.altitude:
                            point = helper.Point(time=currentTimestamp, altitude=int(p.altitude * 3.28084),
                                                 latitude=p.latitude, longitude=p.longitude)
                            h.newPoint(p.src_callsign, point)
                    except fap.DecodeError:
                        # A Decode Error will occur whenever FAP is unable to parse the packet
                        # In this case, check to see if the packet is a GPRMC or PKWDPOS packet
                        gpscompatible = decodeTNC.determineCompatability(out, ["$PKWDPOS", "$GPRMC"])
                        if gpscompatible:
                            # If it is a D710 packet, parse it.
                            latlong = decodeTNC.latlong(out)  # returned as (latitude,longitude)
                            # If we are plotting D710 tracks, Plot it on Google Earth
                            point = helper.Point(time=currentTimestamp, altitude=0, latitude=latlong[1],
                                                 longitude=latlong[0])
                            h.newPoint("D710", point)
                        continue
                    except AttributeError:
                        print "Error in packet"
                        continue

        except serial.SerialException:  # In case off failure, or even a keyboard interrupt, this will shut down the port.
            log.close()
            ser.close()
