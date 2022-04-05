import os
from os import listdir
from os.path import isfile
import subprocess
from datetime import time
from datetime import datetime
import time
from scd30_i2c import SCD30
import requests
from google.oauth2 import service_account

#Testing Import
import random

class SensorBox():
    def __init__(self):
        #I/O Constants
        self.INTERVAL = 1800 #nterval to wait between sensor reads, in seconds
        self.sensor = SCD30()

        self.URL = "https://firestore.googleapis.com/v1/projects/biosensorbox-c9334/databases/(default)/documents/<Date>"
        self.serviceEndpoint = "https://firestore.googleapis.com"
        self.authEndpoint = "https://www.googleapis.com/auth/datastore"
        #Authentication for HTTP requests
        scope = ['https://www.googleapis.com/auth/datastore']
        serviceAccountFile = 'home/pi/biosensorbox-c9334-478a6728ce7e.json'
        #serviceAccountFile = './biosensorbox-c9334-478a6728ce7e.json'
        #This credentials object is the oauth2 that I need to get/extract a token from it and pass that along to the HTTP
        self.credentials = service_account.Credentials.from_service_account_file( serviceAccountFile, scopes=scope)

        #Globals
        self.localData = 0 #If 1, then there is sensor data saved to the disk
        self.logFile = 'home/pi/localFiles/log.txt'
        #self.logFile = './localFiles/log.txt'

    def readSensor(self):
        reading = [3]
        #pull data from sensor
        reading = self.sensor.read_measurement()
        return reading

    def processData(self, reading):
        #If there is data stored to the disk, process it first
        if (self.localData == 1 and self.checkConnection() <= 0):
            self.localData = 0
            self.readFromDisk()
            self.sendToDatabase(reading)
        #Send recent data to database
        if( self.checkConnection() > 0):
            self.saveToDisk(reading)
        else:
            self.sendToDatabase(reading)
            
    def checkConnection(self):
        connection = subprocess.run(['wget', "-q", "--spider", "http://google.com"])
        return connection.returncode

    #Saves the database reading to local disk for retrieval later
    def saveToDisk(self, reading):
        self.localData = 1 #Set the flag notifying the system that there is stored data to be sent
        path = 'home/pi/localFiles/localData.txt'
        #path = './localFiles/localData.txt'
        #Open the local data file, if it does not exist, this also creates it
        localFile = open(path,"a")

        #Write current data reading into a single line of data and indents
        localFile.write( str(reading[0]) + ',' + str(reading[1]) + ',' + str(reading[2]) + ',' + str( datetime.now() ) + '\n' )
        localFile.close()

    #Searches local data file folder, reads every file and outputs it to the database
    def readFromDisk(self):
        file = 'home/pi/localFiles/localData.txt'
        #file = './localFiles/localData.txt'
        with open(file, "r+") as localFile:
            for line in localFile:
                #Read line into a local var, then split it into the list it was made from
                reading = line.split(',')
                #Convert the stored strings back into floating point values
                reading[0] = float(reading[0])
                reading[1] = float(reading[1])
                reading[2] = float(reading[2])
                #Post the stored file into the database, the last entry is the time when the data was originally recorded
                self.sendToDatabase(reading, reading[-1])
                #sleep for three seconds to keep the database from being overwhelmed
                time.sleep(3)
            #Clear the file once all data is extracted by setting the cursor to position 0 and truncating
            localFile.truncate(0)
        localFile.close()


    def sendToDatabase(self, reading, time = str(datetime.now()) ):
        #Assemble API URL and a data object
        documentURL = self.URL + '?documentId=' + time
        data = {
            "fields": {
                "co2": {"integerValue":int(reading[0]) },
                "temp": {"integerValue":int(reading[1]) },
                "humidity": {"integerValue":int(reading[2]) },
                "time": {"stringValue":time }
            }
        }
        #Headers using service account credentials
        headers = {"Bearer": self.credentials.token}

        #createResp = requests.post(self.URL, json=data, headers=headers)
        #createResp = requests.post(self.URL, json=data)
        createResp = requests.post(documentURL, json=data)
        print(createResp.status_code)
        #Output response as a logFile entry
        logFile = open(self.logFile, 'a')
        logFile.write(str(createResp.status_code) + " " + time + "/n")
        logFile.close()

    def run(self):
        #Loop set-up
        self.sensor.set_measurement_interval(self.INTERVAL)
        self.sensor.start_periodic_measurement()

        #Pause until close to XX:00 or XX:30, then enter the loop
        #Expression should give a positive number between 1 and 30
        #sleepTime = 30 - (datetime.now().time().minute % 30 )
        #sleepTime *= 60 #Convert to seconds
        #time.sleep( sleepTime )
        while(True):
            if( self.sensor.get_data_ready() ):
                self.processData( self.readSensor() )
            #Sleep at the end of the loop, as a stopgap
            time.sleep(self.INTERVAL)


def main():
    SB = SensorBox()
    SB.run()

if __name__ == "__main__":
    main()