import serial
import datetime
import time
from glob import glob
import os
import sys

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
                sys.exit()
        elif os.name == "posix":
            try:
                try:
                    ser = serial.Serial("/dev/tty.usbserial")  # Which of these works will determine on which drivers you have
                except serial.serialutil.SerialException:
                    ser = serial.Serial(glob("/dev/tty.PL2303-*")[0])
            except:
                print "Error Connecting to Device"  # If you get this, either the device is not responding or is not plugged in
                sys.exit()
        else:
            print "Unknown operating system"
            sys.exit()

        if not os.path.exists('tnclogs'):
            os.mkdir('tnclogs')

        run_tnc(ser, D710_startup)

        try:
            while 1:
                log = open(os.path.join("tnclogs","tnc.log"), "a")
                got = ser.read()
                out = ""
                while got != "\r":
                    out += got
                    got = ser.read()
                if out != "":
                    currentTimestamp = "# " + str(int(round(time.time()))) + datetime.datetime.now().strftime(" %a %b %d %H:%M:%S %Z %Y")
                    print currentTimestamp
                    print out
                    log.write(currentTimestamp + "\n")
                    log.write(out + "\n")
                    log.flush()
                    log.close()
                    h.submit_packet(out)
        except serial.SerialException:  # In case off failure, or even a keyboard interrupt, this will shut down the port.
            log.close()
            ser.close()
