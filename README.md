# HARBOR-Tracker
### Tracking software for the HARBOR Balloon Project

This repository contains the code for tracking and telemetry of the Weber State University High Altitude Reseach Ballooning for Outreach and Research (HARBOR) project. More information on this project can be found at http://harbor.weber.edu/.

### Function
This software presents an interface to tracking a balloon through the amateur radio APRS format. The intended setup of the system requires a Python-capable computer connected via RS232 to a Kenwood D710 Radio (another radio may be used with a custom start file). The main program then launches a webserver on port 8001 that any computer with access to to the host's IP can access. This webpage displays current information about the balloon (and if available, host radio) and includes the current track plotted on a map of the area.

### Requirements
Running the main program requires several packages:
 * [Python 2.7](http://www.python.org/)
 * USB-to-Serial device drivers (depending on your device)
 * [LeafletJS](http://leafletjs.com/) (See note below)
 * JQuery (See note below)

Further, there are several file dependencies:
 * gmaps.zip - A zip file containing all map tiles the user wishes to be available. More information on this is available in the resources section.
 * audio folder - A folder filled with text-to-speech audio files for non-visual stimulus. More information in the downloads section.

Note: since this is often required to run offline, where users have no live access to javascript libraries, LeafletJS and JQuery must be downloaded and kept in the same folder. Static links for working versions are located in the downloads section.

### Downloads
Static (Dropbox) links to working versions of each of our required files can be found here. Each of these files (unless otherwise specified) can be extracted into the root folder of the repository.
 * [Audio file folder](https://dl.dropboxusercontent.com/u/14409407/EVESign.JPG)
 * [JQuery](https://dl.dropboxusercontent.com/u/14409407/EVESign.JPG)
 * [LeafletJS](https://dl.dropboxusercontent.com/u/14409407/EVESign.JPG)
 * [gmaps.zip](https://dl.dropboxusercontent.com/u/14409407/EVESign.JPG) (for the Uintah Basin area, Utah)

### Resources
Several files in the operation of the tracking system are user specific, and can be generated to meet demands. The most difficult to acquire is the mapping data for your region. The maps required for operation are Google Maps tilesets that are interpreted and displayed by LeafletJS, but must be pre-downloaded for offline users. Maps available from the HARBOR are limited to our range of operations, and may be replaced by another set downloaded by the user.
The tileset downloader can be found here:
[downloadTileSet.py](https://dl.dropboxusercontent.com/u/14409407/EVESign.JPG)
Operation of this file is via command line arguments, and require you to specify your northwest and southeast latitudes and longitudes in decimal degrees format. The format is as follows:
```bash
downloadTileSet.py northlat westlon southlat eastlon
```
If you are experiencing problems IP blocking, this can be expanded to operate on the Tor network (sorry, guys) by launching your Tor client, then modifying line 51 of the downloader, changing *False* to *True*.

### Operation
Setting up the system for tracking is a several step process:
1. Prepare your tracking computer by installing all prerequisites and plug it into a Kenwood D710 via a USB-to-RS232 Serial adapter.
2. Ensure that the D710 is correctly set up for TNC broadcasting of APRS packets (for more information see the manual)
3. Using Command Prompt (Windows), Bash (Unix), or an equivalent, launch the *harbor.py* file.
..* If on Windows, you will be prompted to enter the COM port of the radio interface. This can be found in the Device Manager.
4. Assuming no errors have been listed, the tracking system is now running.
5. In a web browser on the same device type in the web address: <localhost:8001>
..* This step can also be completed on another device on the same network by substituting 'localhost' with the IP address of the host computer.
..* The main index page contains the relevant tracking information and maps. 
6. Specifying settings is done via the *config* page. This is accessed by changing the web address to <localhost:8001/config>.

When adding track metadata via the /config page, you *must* type in values into all fields. (Note that you can autofill the fields by clicking on the links of existing items in the boxes) The attributes section may be any of the attributes for a Leaflet Polyline object, but the most common is 'color'. For example, to change the color of the a track named 'Balloon' to red, the inputs would be:
Field | Value
--- | ---
Track Name: | Balloon
Attribute: | color
Value: | #f00

Several other pages are available for active flight monitoring and debugging. These are:
 * /active - This page shows a list of active callsigns received by the program
 * /meta - JSON string of current state settings made in /config
 * /log - Debugging log of events
 * /tracks - JSON string of current tracked objects
 * /trackdata - JSON string of track points as latitudes and longitudes
 * /info - JSON string of readout values and track points
 
# Contact
To report bugs or request specific features, please use the Github issue tracker for this project, or contact:
 * [Ian Sohl](https://github.com/DocSohl)
 * [Sheyne Anderson](https://github.com/Sheyne)
For queries about the HARBOR project contact:
 * [John Sohl (PI)](http://planet.weber.edu/harbor/contact/default.html)
