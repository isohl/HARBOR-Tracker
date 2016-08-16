"""
decodeTNC.py is a module for a HAM Radio tracking program for the HARBOR High Altitude Balloon Project.
    This module contains functions for the manual decoding of APRS and D710 packets.
    
Ian Sohl
"""
import re

done = False


def delimit(rawdata):
    """Delimit APRS and D710 packets into constituent parts"""
    # For PKWDPOS D710 Packets
    if "PKWDPOS" in rawdata:
        # Split along commas and asterisks
        splitonce = rawdata.split(',')
        splittwice = rawdata[10].split('*')
        # This only works for the North Western Quadrant
        if 'N' in splitonce[4] and 'W' in splitonce[6]:
            returnable = [splitonce[3] + "N", splitonce[5] + "W", "A=" + splittwice[0]]
            return returnable
    # For $GPRMC D710 Packets
    if "GPRMC" in rawdata:
        # Split on commas
        splitonce = rawdata.split(',')
        # If the data matches, return
        if 'N' in splitonce[4] and 'W' in splitonce[6]:
            returnable = [splitonce[3] + "N", splitonce[5] + "W"]
            return returnable
    # For APRS packets (deprecated, use FAP when possible)
    else:
        # Split along the regular expression of /, h and O
        splitonce = re.split('/|h|O', rawdata)
        # Only return if it has the right number of fields
        if len(splitonce) >= 7:
            if 'A=' in splitonce[6]:
                returnable = [splitonce[2], splitonce[3], splitonce[6]]
                return returnable


def latlong(newdata):
    """Return the latitude and longitude of a given packet"""
    # Delimit the data to determine correct chunks
    output = delimit(newdata)
    # Convert latitude and longitude from Degrees:minutes to decimal degrees
    latitude = str(float(output[0][:2]) + (float(output[0][2:7]) / 60))
    longitude = "-" + str(float(output[1][:3]) + (float(output[1][3:8]) / 60))
    # I know, it's terrible...
    return latitude, longitude


def determine_compatability(APRSstring):
    """Determine whether the APRS packet is being tracked and compatible with the parser"""
    return any(APRSstring.startswith(s) for s in ["$PKWDPOS", "$GPRMC"])
