# Sensor-Box-Code
All the code needed to read a Seeed 101020634 combination C02, temperature, and humidity sensor, and to relay that information to an angular firestore database.

# Installation
To install this code on a raspberry pi, wire the pi according to the fritzing diagram and wiring guide included in this repo

Next, save a copy of serviceAccountKey.json to the pi's microSD card. This file includes login credentials for the database, without this file the Pi will be unable to connect to the website. For security reasons, it is not included with the repo, but should be saved locally to existing Pi units.

Once the file is copied over to the Pi, power on the pi, and enter <pip install firebase-admin> onto the Pi's command line. This will install the database's SDK.