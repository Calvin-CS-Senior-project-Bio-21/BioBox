from os import read
import subprocess
from datetime import time
from datetime import datetime
import adafruit_scd30
import board
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import RPi.GPIO as GPIO

#Testing Import
import random

class SensorBox():
    def __init__(self):
        #I/O Constants
        self.PIN = 2 #GPIO pin # to read I2C sensor input
        self.CLK = 3 #GPIO pin # for the I2C clock
        self.INTERVAL = 1800 #nterval to wait between sensor reads, in seconds
        self.sensor = adafruit_scd30.SCD30(board.I2C())

        #MQTT Constants
        self.BROKER = "iot.cs.calvin.edu"
        self.PORT = 1883
        self.USERNAME = "cs326" #TODO: Ask if we can use this
        self.PASSWORD = "piot" #Yeah, that's a plaintext password. I hate it.

        #Globals
        self.localData = 0 #If 1, then there is sensor data saved to the disk
        self.currentDay = datetime.today()

        #fetch credentials for database auth
        self.cred = credentials.Certificate('./serviceAccountKey.json')
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()

    def readSensor(self):
        reading = [3]
        #TODO: pull data from sensor
        debug = 0
        if (debug == 0):
            #random generation for testing
            random.seed()
            reading[0] = random.randint(0, 100)
            reading[1] = random.randint(0, 100)
            reading[2] = random.randint(0, 100)
        else:
            reading[0] = self.sensor.CO2
            reading[1] = self.sensor.temperature
            reading[2] = self.sensor.relative_humidity

        return reading

    def processData(self, reading):
        if( self.checkConnection() > 0):
            self.saveToDisk(reading)
        else:
            self.sendToDatabase(reading)
            
    def checkConnection(self):
        subprocess.run(["wget -q --spider http://google.com"])

    def saveToDisk(self, reading):
        self.localData = 1 #Set the flag notifying the system that there is stored data to be sent


    def sendToDatabase(self, reading):
        if (self.localData == 1):
            self.localData = 0
            #TODO: Figure out how we're storing data locally, and how to dump it all to the database
        else:
            #If we aren't storing data locally, push reading to the database
            doc_ref = self.db.collection(self.currentDay).document(datetime.now())
            doc_ref.set({
                u'Temperature': reading[0],
                u'Humidity': reading[1],
                u'Carbon': reading[2]
            })



    def run(self):
        #Loop set-up
        while(True):
            #Refresh time
            now = datetime.now() #Gets current date and time
            currentTime = time(now.hour, now.minute, now.second) #pairs it down to just a time for comparison
            #Checks to see if we have rolled over to a new day
            #If the days don't match, then either it's the next day, or something is terribly wrong with the universe
            if(now.day != self.currentDay.day ):
                self.currentDay = datetime.today()
            self.processData( self.readSensor() )


def main():
    SB = SensorBox()
    SB.run()

if __name__ == "__main__":
    main()