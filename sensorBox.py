from lib2to3.pgen2 import token
import os
import re
import subprocess
from datetime import time
from datetime import datetime
import time
from scd30_i2c import SCD30
import requests
from oauth2client.service_account import ServiceAccountCredentials
from picamera import PiCamera

class SensorBox():
    def __init__(self):
        #I/O Constants
        self.INTERVAL = 1800 #nterval to wait between sensor reads, in seconds
        self.sensor = SCD30()

        self.URL = "https://firestore.googleapis.com/v1/projects/biosensorbox-c9334/databases/(default)/documents/<Date>/"
        self.serviceEndpoint = "https://firestore.googleapis.com"
        self.authEndpoint = "https://www.googleapis.com/auth/datastore"
        #Authentication for HTTP requests
        scope = ['https://www.googleapis.com/auth/datastore']
        serviceAccountFile = 'home/pi/biosensorbox-c9334-478a6728ce7e.json'
        #serviceAccountFile = './biosensorbox-c9334-478a6728ce7e.json'
        #This credentials object is the oauth2 that I need to get/extract a token from it and pass that along to the HTTP
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name( serviceAccountFile, scope)

        #Globals
        self.localData = 0 #If 1, then there is sensor data saved to the disk
        self.logFile = 'home/pi/localFiles/log.txt'
        self.camera = PiCamera()
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
                self.sendToDatabase(reading, True)
                #sleep for three seconds to keep the database from being overwhelmed
                time.sleep(3)
            #Clear the file once all data is extracted by setting the cursor to position 0 and truncating
            localFile.truncate(0)
        localFile.close()


    def sendToDatabase(self, reading, storedTime=False):
        #If storedTime is true, then the last(4th) entry will have a time stored as a string
        if storedTime:
            CurrentTime = reading[-1]
        else:
            CurrentTime = str(datetime.now())
        print(CurrentTime)
        #Strip the current time to a useful random number for an ID
        mask = re.sub(r"\s+", "", CurrentTime)
        mask = re.sub(r":+", "", mask)
        mask = re.sub(r"\-+", "", mask)
        mask = re.sub(r"\.+", "", mask)
        #Do to a quirk of update masks, the mask needs to have an alphabetic character in there, a purely numeric mask fails
        mask = "A" + mask
        #Assemble the URL and update mask
        updateMask = "?updateMask.fieldPaths=" + mask
        CO2Path = self.URL + "CO2" + updateMask
        tempPath = self.URL + "Temperature" + updateMask
        humPath = self.URL + "Humidity" + updateMask

        #Headers using service account credentials, first refreshes the token
        self.credentials.get_access_token()
        #print(self.credentials.access_token)
        #headers = "Bearer " + self.credentials.access_token

        #Assemble data objects for each reading and append them to the relevant docs.
        COData = {
            "fields":{
                mask:{
                    "mapValue":{
                        "fields":{
                            "CO2": {"doubleValue":reading[0]},   
                            "Time": {"stringValue": CurrentTime}
                        }
                    }
                }
            }

        }
        resp = requests.patch(CO2Path,json=COData) #, headers={"Authorization": headers})
        print(resp.status_code)
        #Output response as a logFile entry
        logFile = open(self.logFile, 'a')
        logFile.write(str(resp.status_code) + " " + CurrentTime + "\n")
        logFile.close()
        time.sleep(3)

        tempData = {
            "fields":{
                mask:{
                    "mapValue":{
                        "fields":{
                            "Temperature": {"doubleValue":reading[1]},   
                            "Time": {"stringValue": CurrentTime}
                        }
                    }
                }
            }
        }
        resp = requests.patch(tempPath,json=tempData) #, headers={"Authorization": headers})
        print(resp.status_code)
        #Output response as a logFile entry
        logFile = open(self.logFile, 'a')
        logFile.write(str(resp.status_code) + " " + CurrentTime + "\n")
        logFile.close()
        time.sleep(3)

        humData = {
            "fields":{
                mask:{
                    "mapValue":{
                        "fields":{
                            "Humidity": {"doubleValue":reading[2]},   
                            "Time": {"stringValue": CurrentTime}
                        }
                    }
                }
            }
        }
        resp = requests.patch(humPath,json=humData) #, headers={"Authorization": headers})
        print(resp.status_code)

        #Output response as a logFile entry
        logFile = open(self.logFile, 'a')
        logFile.write(str(resp.status_code) + " " + CurrentTime + "\n")
        logFile.close()
    
    #Using a raspberry pi spycam, take a photo and store it to home/pi/localFiles/photos/<CurrentTime>.jpg
    def takePhoto(self):
        localFile = 'home/pi/localFiles/images' + str(datetime.now()) + '.jpg'
        #localFile = './localFiles/images' + str(datetime.now()) + '.jpg'
        self.camera.resolution = (1024, 768)
        self.camera.start_preview()
        # Camera warm-up time
        time.sleep(2)
        self.camera.capture(localFile)

    def run(self):
        #Loop set-up
        self.sensor.set_measurement_interval(self.INTERVAL)
        self.sensor.start_periodic_measurement()

        while(True):
            if( self.sensor.get_data_ready() ):
                self.processData( self.readSensor() )
                self.takePhoto()
            #Sleep at the end of the loop, as a stopgap
            time.sleep(self.INTERVAL)


def main():
    SB = SensorBox()
    SB.run()

if __name__ == "__main__":
    main()