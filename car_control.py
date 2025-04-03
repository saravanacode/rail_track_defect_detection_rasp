import RPi.GPIO as GPIO          
from time import sleep

# Define Motor A Pins
in1 = 24
in2 = 23
en1 = 25

# Define Motor B Pins
in3 = 17
in4 = 27
en2 = 22

# Setup GPIO Mode
GPIO.setmode(GPIO.BCM)

# Setup Motor A Pins
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(en1, GPIO.OUT)

# Setup Motor B Pins
GPIO.setup(in3, GPIO.OUT)
GPIO.setup(in4, GPIO.OUT)
GPIO.setup(en2, GPIO.OUT)

# Initialize Motors as Stopped
GPIO.output(in1, GPIO.LOW)
GPIO.output(in2, GPIO.LOW)
GPIO.output(in3, GPIO.LOW)
GPIO.output(in4, GPIO.LOW)

# Setup PWM for Speed Control
pwm1 = GPIO.PWM(en1, 1000)  # Motor A Speed
pwm2 = GPIO.PWM(en2, 1000)  # Motor B Speed

# Start PWM with 25% duty cycle (Low Speed)
pwm1.start(25)
pwm2.start(25)

print("\n")
print("Two Motor Control")
print("Commands: r-run | s-stop | f-forward | b-backward | l-low | m-medium | h-high | e-exit")
print("\n")

while True:
    x = input("Enter Command: ").lower()
    
    if x == 'r':  # Run in last direction
        print("Run Motors")
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)  # Swapped for correction
        GPIO.output(in4, GPIO.HIGH)  # Swapped for correction

    elif x == 's':  # Stop Both Motors
        print("Stop")
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.LOW)

    elif x == 'f':  # Move Forward
        print("Moving Forward")
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)  # Swapped for correction
        GPIO.output(in4, GPIO.HIGH) # Swapped for correction

    elif x == 'b':  # Move Backward
        print("Moving Backward")
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.HIGH)  # Swapped for correction
        GPIO.output(in4, GPIO.LOW)   # Swapped for correction

    elif x == 'l':  # Low Speed
        print("Setting Speed: Low")
        pwm1.ChangeDutyCycle(25)
        pwm2.ChangeDutyCycle(25)

    elif x == 'm':  # Medium Speed
        print("Setting Speed: Medium")
        pwm1.ChangeDutyCycle(50)
        pwm2.ChangeDutyCycle(50)

    elif x == 'h':  # High Speed
        print("Setting Speed: High")
        pwm1.ChangeDutyCycle(75)
        pwm2.ChangeDutyCycle(75)

    elif x == 'e':  # Exit
        GPIO.cleanup()
        print("GPIO Cleaned Up, Exiting...")
        break

    else:
        print("Invalid Command! Please enter a valid command.")
