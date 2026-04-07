#include <Servo.h>

const int NUM_THRUSTERS = 6;

const int thrusterPins[NUM_THRUSTERS] = {5, 3, 6, 9, 10, 11};

Servo thrusters[NUM_THRUSTERS];

const int NEUTRAL_PWM = 1500;
const int MIN_PWM     = 1350;
const int MAX_PWM     = 1650;

const int CLAW_PIN = 12;
const int ROLL_PIN = 13;
const int TILT_PIN = 8;

const int SERVO_MIN = 900;
const int SERVO_MAX = 2100;

Servo clawServo;
Servo rollServo;
Servo tiltServo;

String inputString   = "";
bool   stringComplete = false;

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < NUM_THRUSTERS; i++) {
    thrusters[i].attach(thrusterPins[i]);
    thrusters[i].writeMicroseconds(NEUTRAL_PWM);
  }

  clawServo.attach(CLAW_PIN);
  rollServo.attach(ROLL_PIN);
  tiltServo.attach(TILT_PIN);

  int mid = map(90, 0, 180, SERVO_MIN, SERVO_MAX);
  clawServo.writeMicroseconds(mid);
  rollServo.writeMicroseconds(mid);
  tiltServo.writeMicroseconds(mid);

  inputString.reserve(100);
  Serial.println("ROV Arduino ready");
}

void loop() {
  if (stringComplete) {
    processCommand(inputString);
    inputString    = "";
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
  command.trim();

  if (command.startsWith("THR")) {
    int pwm[NUM_THRUSTERS];
    int lastIndex = 3;

    for (int i = 0; i < NUM_THRUSTERS; i++) {
      int nextSpace = command.indexOf(' ', lastIndex + 1);
      String token  = (i < NUM_THRUSTERS - 1)
                        ? command.substring(lastIndex + 1, nextSpace)
                        : command.substring(lastIndex + 1);
      pwm[i]    = constrain(token.toInt(), MIN_PWM, MAX_PWM);
      lastIndex = nextSpace;
    }

    for (int i = 0; i < NUM_THRUSTERS; i++) {
      thrusters[i].writeMicroseconds(pwm[i]);
    }
    Serial.println("THR OK");
    return;
  }

  int colonIndex = command.indexOf(':');
  if (colonIndex == -1) return;

  String name  = command.substring(0, colonIndex);
  int    angle = constrain(command.substring(colonIndex + 1).toInt(), 0, 180);
  int    us    = map(angle, 0, 180, SERVO_MIN, SERVO_MAX);

  if (name == "claw") {
    clawServo.writeMicroseconds(us);
    Serial.println("claw OK");
  } else if (name == "roll") {
    rollServo.writeMicroseconds(us);
    Serial.println("roll OK");
  } else if (name == "tilt") {
    tiltServo.writeMicroseconds(us);
    Serial.println("tilt OK");
  }
}