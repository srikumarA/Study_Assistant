

#Imports
import time
import pygame
import math

#EYe tracker
import datetime
from csv import writer
import board
import json
import requests

from picamera import PiCamera
from picamera.array import PiRGBArray
import adafruit_character_lcd.character_lcd as character_lcd
import digitalio
import cv2 as cv


headers = {
    "Authorization": "Bearer ya29.a0AX9GBdXgH2Dv4u-CImi2aAGfBBW9LXsvsE1xQCjGpLQTWc-jOw_myXHsn2W1OJikCcccsWaGtKNgvfPB49zGYnY0Nm82B0RFfn6clBY5Bu5HHpVzYzQsWv32jI9CUG7MjuFAbzwrACM3QwCdMf0vDHuzfD9JaCgYKARsSARESFQHUCsbCIXJDUtrT3uFvsa6eFBIgsg0163"
}

para = {
    "name": "Student_record.csv"
}

#initialising cascades for face and eye detection
face_cascade=cv.CascadeClassifier(r'haarcascade_frontalface_default.xml')
eye_cascade=cv.CascadeClassifier(r'haarcascade_eye_tree_eyeglasses.xml')

#configuring lcd input output
lcd_rs = digitalio.DigitalInOut(board.D12)
lcd_en = digitalio.DigitalInOut(board.D7)
lcd_d4 = digitalio.DigitalInOut(board.D8)
lcd_d5 = digitalio.DigitalInOut(board.D25)
lcd_d6 = digitalio.DigitalInOut(board.D24)
lcd_d7 = digitalio.DigitalInOut(board.D23)
lcd_backlight = digitalio.DigitalInOut(board.D2)
lcd_cols=20
lcd_rows=4
lcd=character_lcd.Character_LCD_Mono(lcd_rs,lcd_en,lcd_d4,lcd_d5,lcd_d6,lcd_d7,lcd_cols,lcd_rows,lcd_backlight)
lcd.cursor_position(4,1)
lcd.message="StandBy Mode"
# switch setup
pygame.mixer.init()
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(20,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
#initialize camera
camera=PiCamera()
camera.resolution=(640,480)
camera.framerate=32
global eye_close_1
eye_close_1=False
global time_iclose
global count
count=0
global prev
prev=None
global start_min

global rem_given
rem_given=False
def dist_calculator(x1,y1,x2,y2):
    dist=math.sqrt((y2-y1)**2+(x2-x1)**2)
    return dist




while True:
    List = []
    if GPIO.input(21)==GPIO.HIGH:
        pygame.mixer.music.load("session_start.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() == True:
            continue
        lcd.clear()
        lcd.cursor_position(4,1)
        lcd.message="Study time"
        start_min=datetime.datetime.now().minute
        List+=[datetime.datetime.now().date()]
        List+=[datetime.datetime.now().strftime("%H:%M:%S")]
        #initialising opencv
        #vid=cv.VideoCapture(0)
        raw_cap=PiRGBArray(camera,size=(640,480))
        for frame in camera.capture_continuous(raw_cap,format='bgr'):
            frame=frame.array
            h,w=frame.shape[:2]

            #eye and face tracking requires gray scale image
            frame_gray=cv.cvtColor(frame,cv.COLOR_BGR2GRAY)


            # face
            faces = face_cascade.detectMultiScale(frame_gray, 1.3, 5)


            if len(faces) == 0:
                count+=1
                lcd.clear()
                lcd.cursor_position(4, 1)
                lcd.message = "Bad Posture"

            else:
                count=0
                lcd.clear()
                str_time=datetime.datetime.now().strftime("%H:%M:%S")
                lcd.cursor_position(5, 1)
                lcd.message=str_time


            if count<1000:
                #eye tracker
                #eyes=eye_cascade.detectMultiScale(frame_gray,1.3,5)
                del_x=0
                del_y=0
                eyes=[]
                for (xe,ye,we,he) in eyes:
                    if del_x ==0 and del_y==0:
                        del_x =xe
                        del_y =ye
                    else:
                        del_x-=xe
                        del_y-=xe
                if len(eyes)==0 and eye_close_1!=True:
                    eye_close_1=True
                    time_iclose=datetime.datetime.now().minute
                else:
                    eye_close_1=False
                    time_iclose=None

                if time_iclose!=None and (datetime.datetime.now().minute-time_iclose)%60>=1:
                    lcd.cursor_position(4,1)
                    lcd.message="Warning!!!"
                    if (datetime.datetime.now().minute-time_iclose)%60>=5:

                        break
                #reminder
                if (datetime.datetime.now().minute-start_min)%60>=1 and not rem_given:   #40 instead of 1
                    pygame.mixer.music.load("Do you want a break.mp3")
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy() == True:
                        continue
                    lcd.message="Do you want to take water break?"
                    time.sleep(5)
                    if GPIO.input(20) == GPIO.HIGH:
                        rem_given = True
                        lcd.clear()
                        lcd.cursor_position(4,1)
                        lcd.message="Break Time"
                        time.sleep(20)     #300 instead of 20
                        pygame.mixer.music.load("break_time_ends.mp3")
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy() == True:
                            continue
                        lcd.clear()
                        lcd.cursor_position(4, 1)
                        lcd.message = "Break Time Ends"
                        time.sleep(5)
                    else:
                        rem_given = False
                        start_min = (start_min + 1) % 60#30 instead 1
                        pygame.mixer.music.load("Skipped_break.mp3")
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy() == True:
                            continue

            if  count > 1000 or GPIO.input(21) == GPIO.HIGH:
                break
            raw_cap.truncate(0)
        lcd.clear()
        lcd.cursor_position(4, 1)
        lcd.message="Session over!"
        pygame.mixer.music.load("session_ends.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() == True:
            continue
        time.sleep(2)
        List += [datetime.datetime.now().strftime("%H:%M:%S")]
        with open(r'/home/pi/event.csv','a+') as f_object:
            write_object = writer(f_object)
            write_object.writerow(List)
            f_object.close()
        files = {
            'data': ('text/csv', json.dumps(para), 'application/json;charset=UTF-8'),
            'file': open(r"/home/pi/event.csv", 'rb')
        }

        r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                          headers=headers,
                          files=files,
                          )
    #technical loophole
    elif GPIO.input(20) == GPIO.HIGH:
        break



