#include <Wire.h>
#include "MS5837.h"
#define IN1_PIN 6 // Motor control pin 1
#define IN2_PIN 11 // Motor control pin 2

MS5837 sensor;

// Define variables
const long interval = 5000;            // interval to send readings
unsigned expandtime = 18000;           // time to expand
long waitTime = 0;                     // wait time between expanding and contracting - set by message sent
unsigned long previousMillisFloat = 0; // timer for float expansion/stopping
bool floatIsStopped = true;
char nextCommand = 's';
int datacount = 0;
unsigned long previousMillis = 0;      // counter used to time readings being sent

// Arrays to store readings
int pressureReadings[150];
int timeReadings[150];
int depthReadings[150];

// Structs to match original data format
typedef struct control_message {
  char c;
  int val;
} control_message;

typedef struct send_message {
  int p;
  int d;
  int t;
} send_message;

control_message ControlData;
send_message sendReadings;

void setup() {
  // Init Serial Monitor
  Serial.begin(9600);
  Serial.println("Underwater Float Controller - Serial Version");
  
  // Set motor control pins as output
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
  stop(1000);
  
  Wire.begin();
  delay(100);

  Wire.setClock(1);

  // Initialize pressure sensor
  // Returns true if initialization was successful
  /*
  while (!sensor.init()) {
    Serial.println(sensor.init());
    Serial.println("Init failed!");
    Serial.println("Are SDA/SCL connected correctly?");
    Serial.println("Blue Robotics Bar30: White=SDA, Green=SCL\n");
    delay(5000);
  }*/

  // .init sets the sensor model for us but we can override it if required.
  sensor.setModel(MS5837::MS5837_02BA);
  sensor.setFluidDensity(997); // kg/m^3 (freshwater, 1029 for seawater)
  
  Serial.println("Setup complete. Ready to receive commands.");
  Serial.println("Commands: 'f' (forward), 'b' (back), 's' (stop), 't' (set expand time)");
  Serial.println("Format: [command][value] (e.g., 'f5000' for forward with 5000ms wait time)");
}

void stop(int val) {
  if (!floatIsStopped) {
    Serial.println("Stopping");
    digitalWrite(IN1_PIN, LOW);
    digitalWrite(IN2_PIN, LOW);
    floatIsStopped = true;
    delay(val);
  }
}

void backwards(int val) {
  Serial.println("Moving back");
  floatIsStopped = false;
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, HIGH);
  delay(val);
  //movePulse(val);
}

void forward(int val) {
  Serial.println("Moving forward");
  floatIsStopped = false;
  digitalWrite(IN1_PIN, HIGH);
  digitalWrite(IN2_PIN, LOW);
  delay(val);
  //movePulse(val);
}

void sendSerialData(int index) {
  // Format: P:[pressure],D:[depth],T:[time]
  Serial.print("DATA,");
  Serial.print(pressureReadings[index]);
  Serial.print(",");
  Serial.print(depthReadings[index]);
  Serial.print(",");
  Serial.println(timeReadings[index]);
}

void loop() {
  // Process any incoming serial commands
  processSerialCommand();

  unsigned long currentMillis = millis();
  
  // Stop after expandtime has elapsed
  if (currentMillis - previousMillisFloat >= expandtime && !floatIsStopped) {
    stop(1000);
  }

  // Execute next command after wait time
  if (currentMillis - previousMillisFloat >= (waitTime + expandtime)) {
    if (nextCommand == 'f') {
      forward(1000);
      previousMillisFloat = millis();
    } else if (nextCommand == 'b') {
      backwards(1000);
      previousMillisFloat = millis();
    } else if (nextCommand == 's') {
      stop(1000);
    }
    nextCommand = 's';
  }

  // Send sensor readings periodically
  if (currentMillis - previousMillis >= interval){
    previousMillis = currentMillis;
    
    // Read sensor data
    sensor.read();
    
    // Store readings in arrays
    pressureReadings[datacount] = int(round(sensor.pressure() * 100));
    depthReadings[datacount] = int(round(sensor.depth() * 100));
    timeReadings[datacount] = int(round(millis() / 100));
    
    // Send readings over Serial

    sendSerialData(datacount);
    
    // Increment data count (with wrap-around)
    datacount = (datacount + 1) % 150;
  }
}

void runFloat(){
  backwards(10000);
  sensor.read();
  pressureReadings[datacount] = int(round(sensor.pressure() * 100));
  depthReadings[datacount] = int(round(sensor.depth() * 100));
  timeReadings[datacount] = int(round(millis() / 100));
  sendSerialData(datacount);
  datacount = (datacount + 1) % 150;
  forward(10000);
}

void movePulse(int pwm){
    digitalWrite(IN1_PIN,HIGH);
    delay(20); // between pulses
    digitalWrite(IN1_PIN,LOW);
    delayMicroseconds(pwm);
}

void processSerialCommand() {
  if (Serial.available() > 0) {
    String cmd = Serial.readString();
    
    /*
    // Skip whitespace and newlines
    while (Serial.available() > 0 && (Serial.peek() == ' ' || Serial.peek() == '\n' || Serial.peek() == '\r')) {
      Serial.read();
    }
    
    int idx = 0;
    for(auto x : cmd){
      if(x == ' ' || x == '\n' || x == '\r'){
        cmd.remove(idx);
      }
      idx++;
    }*/

    int value = (cmd.substring(1)).toInt();
    cmd = cmd.substring(0, 1);
    
    Serial.print("Received command: ");
    Serial.print(cmd);
    Serial.print(" Value: ");
    Serial.println(value);
    
    if (cmd == 't') {
      expandtime = value;
    } else {
      waitTime = value;
      previousMillisFloat = millis();
    }
    
    if (cmd == "f") {
      forward(value);
      nextCommand = "b";
    } else if (cmd == "b") {
      backwards(value);
      nextCommand = "f";
    } else if (cmd == "s") {
      stop(value);
      nextCommand = "s";
    } else if(cmd == "r"){
      runFloat();
    }
  }
}