#include <Servo.h>

Servo tiltServo;

const int TILT_PIN = 8;   // CHANGE if wired differently
const int SERVO_MIN = 900;
const int SERVO_MAX = 2100;

String inputString = "";
bool stringComplete = false;

void setup() {
  Serial.begin(9600);

  tiltServo.attach(TILT_PIN);

  // Start centered
  int midpoint = map(90, 0, 180, SERVO_MIN, SERVO_MAX);
  tiltServo.writeMicroseconds(midpoint);

  inputString.reserve(50);
  Serial.println("Camera Servo Ready");
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
  // Expected format: tilt:90
  int colonIndex = command.indexOf(':');
  if (colonIndex == -1) return;

  String name = command.substring(0, colonIndex);
  int angle = command.substring(colonIndex + 1).toInt();
  angle = constrain(angle, 0, 180);

  if (name == "tilt") {
    int us = map(angle, 0, 180, SERVO_MIN, SERVO_MAX);
    tiltServo.writeMicroseconds(us);
    Serial.println("Tilt moved to " + String(angle));
  }
}
