#include <Servo.h>

const int NUM_THRUSTERS = 6;

/*
 Thruster order (make it match the Python):
 0 - FR
 1 - FL
 2 - BR
 3 - BL
 4 - F  (vertical front)
 5 - B  (vertical back)
*/
const int thrusterPins[NUM_THRUSTERS] = {2, 3, 4, 5, 6, 7};

Servo thrusters[NUM_THRUSTERS];

const int NEUTRAL_PWM = 1500;
const int MIN_PWM = 1350;
const int MAX_PWM = 1650;

String inputString = "";
bool stringComplete = false;

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < NUM_THRUSTERS; i++) {
    thrusters[i].attach(thrusterPins[i]);
    thrusters[i].writeMicroseconds(NEUTRAL_PWM);
  }

  inputString.reserve(100);
  Serial.println("Thrusters Arduino ready");
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
  if (!command.startsWith("THR")) return;

  int pwm[NUM_THRUSTERS];
  int lastIndex = 3; // after "THR"

  for (int i = 0; i < NUM_THRUSTERS; i++) {
    int nextSpace = command.indexOf(' ', lastIndex + 1);
    String value = (i < NUM_THRUSTERS - 1)
                   ? command.substring(lastIndex + 1, nextSpace)
                   : command.substring(lastIndex + 1);

    pwm[i] = constrain(value.toInt(), MIN_PWM, MAX_PWM);
    lastIndex = nextSpace;
  }

  for (int i = 0; i < NUM_THRUSTERS; i++) {
    thrusters[i].writeMicroseconds(pwm[i]);
  }

  Serial.println("Thrusters updated");
}
