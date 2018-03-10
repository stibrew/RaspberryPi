#########################################################################################
# Title: Motion detection using Raspberry Pi and Image
# Author: Siddhant Tibrewal
# Brief description: 
# This script uses PiCamera and OpenCV in order to detect motion
# When the motion is detected, 20 second long video will be saved to $HOME/recordings
# The foreground extraction algorithm is based on differential imaging 
# Play around with the control parameters in order to achieve the desired result
# The parameters in this script are tuned for bird watching
# Quit the program by hitting the escape key
#########################################################################################

from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import time
import datetime
from os.path import expanduser

# Size of the image to be used for the processing
width = 1024 #pixels
height = 720 #pixels

# Video capture settings
recordingTime = 20 #seconds
pathToHome = expanduser("~")

# Motion detection threshold should be 0.25 percent of the image size
percentMotion = 0.0025
kernelSize = 3 #pixels

# Book keeping variables for running stablisation
firstRun = True
frameCountTillStablised = 50
frameCount = 0
stablised = False

# Interfacing with the raspberry pi camera
camera = PiCamera()
camera.resolution = (width, height)
camera.framerate = 25
rawCapture = PiRGBArray(camera, size=(width, height))

# Named openCV window
display_window = cv2.namedWindow("Thresholded image")
time.sleep(1)

# Helper function to calculate the difference image stablised over three frames
def diffImg(t0, t1, t2):
  d1 = cv2.absdiff(t2, t1)
  d2 = cv2.absdiff(t1, t0)
  return cv2.bitwise_and(d1, d2)

# Main loop to run the motion detection
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    
    # Dirty hack: get dummy first frames in order to avoid memory problems
    if firstRun:
        frame_minus_1 = cv2.cvtColor(frame.array, cv2.COLOR_RGB2GRAY)
        frame_0 = frame_minus_1
        frame_plus_1 = frame_0
        firstRun = False
        
    # Calculate the difference image
    diffImage = diffImg(frame_minus_1, frame_0, frame_plus_1)

    # Update the background and foreground images
    frame_minus_1 = frame_0
    frame_0 = frame_plus_1
    frame_plus_1 = cv2.cvtColor(frame.array, cv2.COLOR_RGB2GRAY)
    
    # Threshold the image in order to get only the movement in the foreground with gray value 255
    _,thresholdedImage = cv2.threshold(diffImage, 0, 255, cv2.THRESH_OTSU)
    
    # Erode the thresholded image to remove the noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernelSize,kernelSize))
    thresholdedImage = cv2.erode(thresholdedImage, kernel, iterations = 1)
    
    # Capture a video if motion was detected and the stream was stablised
    nonZeroCnt = cv2.countNonZero(thresholdedImage)
    
    # Print out the count of pixels "moved in" the image
    print ("White pixel count: "), nonZeroCnt
    
    if stablised == True and nonZeroCnt > height*width*percentMotion:
        timeStamp = datetime.datetime.now().strftime('%Y%m%d_%Hh%Mm%Ss')
        print ("Motion detected: "), timeStamp
        camera.start_recording(pathToHome + '/recordings/' + timeStamp + '.h264')
        camera.wait_recording(recordingTime)
        camera.stop_recording()
        frameCount = 0
        stablised = False
    
    # Display an image for debugging reasons
    # cv2.imshow("Frame", frame.arra)yif
    cv2.imshow("Thresholded image", thresholdedImage)

    key = cv2.waitKey(1)
    rawCapture.truncate(0)
    
    if frameCount != frameCountTillStablised:
        frameCount += 1
    else:
        stablised = True

    # If keyboard interrupt is provided, free the objects and exit
    if key == 1048603:
        camera.close()
        cv2.destroyAllWindows()
        break