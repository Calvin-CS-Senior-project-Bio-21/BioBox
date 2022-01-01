#include <thread>
#include <stdlib.h>
#include <chrono>
#include <pigpiod_if2.h>
#include <string>
#include <Adafruit_SCD30.h>
#include <client.h>

using namespace std;
using namespace std::this_thread;
using namespace std::chrono;

//I/O consts
const PIN = 2; //GPIO pin # to read I2C sensor input
const CLK = 3; //GPIO pin # for the I2C clock 
const INTERVAL = 1800; //Interval to wait between sensor reads, in seconds
//Program Consts
const DEBUG = 1; //Outputs debug info to the console, and skips
//MQTT Consts
const BROKER = "iot.cs.calvin.edu";
const PORT = 1883;
const USERNAME = "cs326"; //TODO: Ask if we can use this
const PASSWORD = "piot"; //Yeah, that's a plaintext password. I hate it.

//Globals
int localData = 0; //If 1, then there is sensor data saved to the disk
int daemon = -1;   //ID number for Pigpio library, used to identify connected Pi, and interact with I/O
Adafruit_SCD30 sensor;

//MQTT Broker
broker = mqtt::client::client(BROKER, "sensor_box_pi"); //I think this might work. I don't really know...

//Reads temp, humidity, and CO2 data from sensor, in that order
int[] readSensor() {
    int reading [3];
    //If debug is 1, output an array of random numbers
    if ( DEBUG == 1) {
        reading[0] = rand() % 100 + 1;
        reading[1] = rand() % 100 + 1;
        reading[2] = rand() % 100 + 1;
    }
    
    try {
        //gpio_read(daemon, PIN);
        reading[0] = this.sensor.temperature;
        reading[1] = this.sensor.relative_humidity;
        reading[2] = this.sensor.CO2;
    }
    return reading;
}

//Reads data from sensor, checks for a wifi connection, and routes data accordingly
void processData( int reading[] ) {
    //Checks Wifi connection, a return value of 0 means we are connected
    if(checkConnection() > 0) {
        saveToDisk(reading);
    } else {
        sendToDatabase(reading);
    }
}

//Checks for an internet connection on the Pi, returns 0 if a connection exists
int checkConnection() {
    //The following system call sends a web spider to attempt to connect to google.
    //If it returns anything else besides a 0, the device is not connected to the internet
    return system("wget -q --spider http://google.com");
}

//Connects and sends sensor readings to Cloud Firestore database via an mqtt connection to our website
void sendToDatabase( int reading[] ) {
    //connects to broker
    this.broker.connect();

    this.broker.publish();

    
}

//Saves data locally on the Pi, and raises a flag to alert the program that the connection to internet has been severed
void saveToDisk( int reading[] ) {
    localData = 1;  //Set the flag notifying the system that there is stored data to be sent
    
}

int main() {
    //Loop set-up
    //Start Pigpio daemon
    //daemon = pigpio_start(NULL,NULL);
    //Set the mode of the PIN and CLOCK GPIO pins
    set_mode(daemon, PIN, PI_INPUT);
    set_mode(daemon, CLK, PI_OUTPUT);
    //Start the clock pin
    
    //Main loop, reads sensor input once every 30 minutes
    while (true){
        //Reads data from sensor and immediately pass it to be processed
        processData( readSensor() );
        /*
            I think for a more reactive check of network connection, I should keep looping, checking for wifi instead of sleeping
        */
        //Finally, sleep the thread for INTERVAL seconds
        sleep_for(seconds(INTERVAL));
    }
    //Clean-up and exit
    pigpio_stop(daemon);
    exit(0);
}