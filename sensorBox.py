from os import listdir
from os.path import isfile
import subprocess
from datetime import time
from datetime import datetime
from scd30_i2c import SCD30
import os
#import firebase_admin
#from firebase_admin import credentials
#from google.cloud import firestore
#from firebase_admin import firestore

#Testing Import
import random

class SensorBox():
    def __init__(self):
        #I/O Constants
        self.PIN = 2 #GPIO pin # to read I2C sensor input
        self.CLK = 3 #GPIO pin # for the I2C clock
        self.INTERVAL = 1800 #nterval to wait between sensor reads, in seconds
        self.sensor = SCD30()

        #Globals
        self.localData = 0 #If 1, then there is sensor data saved to the disk
        self.currentDay = datetime.today()

        #fetch credentials for database auth
        #self.cred = credentials.Certificate('./serviceAccountKey.json')
        #firebase_admin.initialize_app(self.cred)
        #self.db = firestore.client()

    def readSensor(self):
        reading = [3]
        #pull data from sensor
        reading = self.sensor.read_measurement()
        debug = 1
        if (debug == 0):
            #random generation for testing
            random.seed()
            reading[0] = random.randint(0, 100)
            reading[1] = random.randint(0, 100)
            reading[2] = random.randint(0, 100)
            print(reading)
        else:
            pass
        
        print("reading is: ")
        print(reading)
        return reading

    def processData(self, reading):
        if( self.checkConnection() > 0):
            self.saveToDisk(reading)
        else:
            pass
            #self.sendToDatabase(reading)
            
    def checkConnection(self):
        #subprocess.run(["wget -q --spider http://google.com"])
        connection = subprocess.run(['wget', "-q", "--spider", "http://google.com"])
        return connection.returncode

    #Saves the 
    def saveToDisk(self, reading):
        self.localData = 1 #Set the flag notifying the system that there is stored data to be sent
        #path = '\localFiles\\' + self.currentDay
        path = '/localFiles/localData.txt'
        #Open the local data file, if it does not exist, this also creates it
        localFile = open(path,"w")

        #Write current data reading into a single line of data
        localFile.write( reading[0] + ',' + reading[1] + ',' + reading[2])
        localFile.close()

    #Searches local data file folder, reads every file and outputs it to the database
    def readFromDisk(self):
        fileList = listdir('/localFiles/')
        for file in fileList:
             if isfile(file):
                with open(file, "r") as localFile:
                    for line in localFile:
                        #Read line into a local var, then split it into the list it was made from
                        reading = line.split(',')
                        #Post the stored file into the database
                        self.sendToDatabase(reading)
                localFile.close()


    def sendToDatabase(self, reading):
        if (self.localData == 1):
            self.localData = 0
            self.readFromDisk()
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
        self.sensor.set_measurement_interval(self.INTERVAL)
        self.sensor.start_periodic_measurement()

        while(True):
            #Refresh time
            now = datetime.now() #Gets current date and time
            currentTime = time(now.hour, now.minute, now.second) #pairs it down to just a time for comparison
            #Checks to see if we have rolled over to a new day
            #If the days don't match, then either it's the next day, or something is terribly wrong with the universe
            if(now.day != self.currentDay.day ):
                self.currentDay = datetime.today()
            if( self.sensor.get_data_ready() ):
                self.processData( self.readSensor() )


def main():
    SB = SensorBox()
    SB.run()

if __name__ == "__main__":
    main()