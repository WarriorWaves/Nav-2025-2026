#include <Servo.h>

Servo esc;

int potPin = A0;
int potValue;
int escValue;

void setup() {
  esc.attach(9);
  Serial.begin(9600);


  Serial.println("Arming ESC...");
  esc.writeMicroseconds(1000); 
  delay(3000);
  Serial.println("ESC Armed!");
}

void loop() {
  potValue = analogRead(potPin);

  escValue = map(potValue, 0, 1023, 1000, 2000);

  esc.writeMicroseconds(escValue);

  Serial.print("Pot: ");
  Serial.print(potValue);
  Serial.print(" -> ESC: ");
  Serial.println(escValue);

  delay(20); // Small delay for stability
}
