# Sensor-Box-Code
All the code needed to read a Seeed 101020634 combination C02, temperature, and humidity sensor, and to relay that information to an angular firestore database.

# Installation
To install this code on a raspberry pi, wire the pi according to the fritzing diagram and wiring guide included in this repo

Once the file is copied over to the Pi, power on the pi, and enter <pip install firebase-admin> onto the Pi's command line. This will install the database's SDK.

# Setting up the Pi
1. Start by downloading and running the Raspberry Pi imager here: [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/)
2. Install a copy of Raspberry Pi OS Lite (32-bit) under the Raspberyy Pi OS (other) category
3. Install the OS onto the inserted SD card
    -Note that due to a strange hardware bug on window's SD card readers, there is a small chance doing this will crash your computer, usually once the status bar is marked as complete, if this happens, reboot and eject the SD card, it finished copying the OS properly, its just that some SD card readers have a design flaw that causes this crash.

3. Connect the sensor to the Pi's pins according to SensorBox_bb.PNG, using pinout-.jpg as a guide if needed.
4. Connect the camera to the Pi by pulling the black tab on the slot opposite the micro-usb slot, and inserting the camera's cable so the lens faces upwards
5. Connect the Pi to a monitor and keyboard using a HDMI to micro HDMI cord, and a USB to micro USB adapter, and power it on

At this point, everything else needs to be done on the raspberry pi itself, so the next instructions will be for command line set-up.

# Command Line
Note: This section provides my best guess on how to set up wifi using only a Raspberry Pi Zero W. Initially, wifi was set up using a Raspberry Pi 3, if these instructions fail on the provided Pi zeros, it may be possible to borrow a Pi 3 from Professor Schuurman. 

To log into the pi for the first time, use the default username/password of pi/raspberry.
To change this, run the command <passwd> and follow the prompts

# Wifi
If this is necessary, repeat these instructions with the SD card plugged into a Pi 3, and start by connecting it to ethernet.
1. Type <sudo nano /etc/network/interfaces> and add the following block of code below the pound signs:
<iface eth0 inet manual
allow-hotplug wlan0
iface wlan0 inet dhcp
    wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf>

2. Press ctrl+S to save the file, and ctrl+X to exit nano
3. a. To generate an NTHASH of a password, run <echo -n <password> | iconv -t utf16le | openssl md4> on the main command line. Make a note of the output.
3. b. Run <sudo nano /etc/wpa_supplicant/wpa_supplicant.conf> and at the bottom of the file add the following:
<ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
ctrl_interface_group=0
update_config=1
country=US
network={
      ssid="eduroam"
      scan_ssid=1
      key_mgmt=WPA-EAP
      eap=PEAP
      identity="username@students.calvin.edu"
      password=hash:<HashValue>           <--- NTHASH of password -- fill in with your generated one from above
      phase2="MSCHAPV2"
   }>

4. Run <sudo reboot> to turn the pi off and back on again. 

Note: As of right now, the password hash present in the Pi is a hash of my password, which is expiring soon, and can either be replaced with another student's email password, or by a CIT generated password. However, the former option is a lot easier.

# Packages
    Next, we have to install all relevant packages our program uses.
0. Run <sudo apt-get update>, then <sudo apt-get upgrade> to ensure the OS is up to date, this will take a while.
1. Run <sudo pip install requests>
2. Run <sudo pip install scd30_i2c>
3. Run <sudo pip install oauth2client>
4. Run <sudo pip install subprocess>
5. Run <sudo  pip install picamera>

# App set-up
1. in the home directory, run <mkdir localFiles>, this is a directory the program expects to exist.
2. without changing directory, run <mkdir localFiles/images>, this is another directory the program expects to exist.
3. Run <ifconfig> and note the ip address for wlan0
4. Run <sudo raspi-config> and using the arrow keys, navigate to "Interface Options", and press enter.
5. Navigate to "I2 SSH" and press enter, enable SSH and press "Yes" when prompted. Wait until a notification saying SSH has been enabled appears.
6. Navigate back to "Interface Options" and select "I2C" and similarly enable it like you did with SSH
7. Navigate back to "Interface Options" and select "Legacy camera" and similarly enable it like you did with SSH
8. Select "Finish" and exit the config tool.

# Copying the application to the Pi
These instructions are to be done on your main PC where a copy of sensorBox.py is downloaded. These instrucitons also assume that the program is in the downloads folder on the C: drive of a windows machine, and that windows powershell is being used.
If this is not the case, <cd D:> or <cd <Drive Letter>> will switch to the proper drive, and any instance of <.\Downloads> can be changed to a path to the correct folder.

1. run <cd .\Downloads>
2. run <scp .\sensorBox.py pi@<Recorded IP Address>:./>

# Setting up the program to start at runtime
These instructions are to be done back on the pi connected to a keyboard or monitor. In this section, you will make a new systemd service to run sensorBox.py at start up.
1. run <sudo nano /etc/systemd/system/sensor.service>
2. In the editor, type the following text, note that it is case sensitive:

[Unit]
Description=sensor service
After=network-online.target
[Service]
ExecStart=/usr/bin/python3 /home/pi/sensorBox.py
Restart=always

[Install]
WantedBy=multi-user.target
3. Enter ctrl+S to save, and ctrl+X to exit Nano.
4. Restart the system's service manager with <sudo systemctl daemon-reload>
5. Enable the new service with <sudo systemctl enable sensor.service>
6. Turn off the pi with <sudo halt>, and disconnect it from the keyboard and monitor, next time it is powered on, the script should start at launch.

Note- Copying over files can be done in a single SCP command, no need to ssh into the pi, then scp out of the pi. Just give those instructions in one line here.

# Retrieving images
These steps are to be done on a regular desktop

Running the command <scp -r pi@<IP address>:./localFiles/images> on a powershell or bash terminal will retrieve the images from the pi.
Running <ssh -e "rm ./localFiles/images"> to clear the cache of images, and prevent storage from filling up