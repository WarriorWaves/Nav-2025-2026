#include <Servo.h>

Servo clawServo;
Servo rollServo;

const int clawPin = 10;
const int rollPin = 9;

// Savox SW-0250MG pulse range
const int SERVO_MIN = 900;
const int SERVO_MAX = 2100;

String inputString = "";
bool stringComplete = false;

void setup() {
  Serial.begin(9600);

  clawServo.attach(clawPin);
  rollServo.attach(rollPin);

  clawServo.writeMicroseconds(1500); // midpoint
  rollServo.write(90);                // midpoint

  inputString.reserve(50);
  Serial.println("Arduino ready");
}

void loop() {
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}

void processCommand(String command) {
  int colonIndex = command.indexOf(':');
  if (colonIndex == -1) return;

  String servoName = command.substring(0, colonIndex);
  int targetPos = command.substring(colonIndex + 1).toInt();
  targetPos = constrain(targetPos, 0, 180);

  if (servoName == "claw") {
    int us = map(targetPos, 0, 180, SERVO_MIN, SERVO_MAX);
    clawServo.writeMicroseconds(us);
  } else if (servoName == "roll") {
    rollServo.write(targetPos);
  }
}
