import cv2 as cv
import mediapipe as mp
import time
import requests
from datetime import datetime
import pytz


class poseDetector:
    def __init__(self):
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose()
        self.mpDraw = mp.solutions.drawing_utils

    def findPose(self, img, draw=True):
        if len(img.shape) == 2:  # Check if the image is grayscale
            imgRGB = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
        else:
            imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)

        self.results = self.pose.process(imgRGB)
        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(img, self.results.pose_landmarks,
                                           self.mpPose.POSE_CONNECTIONS)
        return img

    def findPosition(self, img, draw=True):
        self.lmList = []
        if self.results.pose_landmarks:
            myPose = self.results.pose_landmarks
            for id, lm in enumerate(myPose.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv.circle(img, (cx, cy), 4, (0, 225, 0), cv.FILLED)
        return self.lmList


def send_msg(text, image_path=None):
    token = "Your telegram token"
    chat_id = "your own chat id"

    # Get current time in IST
    current_time_utc = datetime.utcnow()
    tz_ist = pytz.timezone('Asia/Kolkata')
    current_time_ist = current_time_utc.replace(tzinfo=pytz.utc).astimezone(tz_ist)
    hours, minutes, seconds = current_time_ist.hour, current_time_ist.minute, current_time_ist.second
    time_text = "{}:{}:{} IST".format(hours, minutes, seconds)

    # Add current time text to the message
    text_with_time = f"{text}\n\n{time_text}"

    # Send message
    url_req = "https://api.telegram.org/bot" + token + "/sendMessage"
    data = {'chat_id': chat_id, 'text': text_with_time}
    requests.post(url_req, data=data)

    # Send image if provided
    if image_path:
        # Read the image
        img = cv.imread(image_path)

        # Draw current time text on the image
        cv.putText(img, time_text, (10, 70), cv.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        # Save the modified image
        modified_image_path = "modified_detected_person_image.jpg"
        cv.imwrite(modified_image_path, img)

        # Send the modified image
        url_req = "https://api.telegram.org/bot" + token + "/sendPhoto"
        files = {'photo': open(modified_image_path, 'rb')}
        requests.post(url_req, data=data, files=files)


def main():
    pTime = 0
    cTime = 0
    # cap = cv.VideoCapture(0)
    cap = cv.VideoCapture("Culprit_detected.mp4")
    # cap =  cv.VideoCapture("CCTV footage -2.mp4")
    #cap = cv.VideoCapture("cctv1.mp4")
    # cap = cv.VideoCapture("flood.mp4")
    # cap = cv.VideoCapture(0)
    detector = poseDetector()

    send_msg("--------------------------------------------------------------------")

    tTime = 0
    x, y = 0, 0
    while True:
        success, img = cap.read()
        img = detector.findPose(img)
        lmList = detector.findPosition(img, draw=True)

        cTime = time.time()
        current_time_utc = datetime.utcnow()
        tz_ist = pytz.timezone('Asia/Kolkata')
        current_time_ist = current_time_utc.replace(tzinfo=pytz.utc).astimezone(tz_ist)
        hours, minutes, seconds = current_time_ist.hour, current_time_ist.minute, current_time_ist.second

        if len(lmList) != 0:
            _, x, y = lmList[0]
            if cTime - tTime > 5:
                text = "Alert!!!!!!!!!Person detected at camera pixel\n" + \
                       "Time: {}:{}:{} IST\n{},{}".format(hours, minutes, seconds, x, y)
                image_path = "detected_person_image.jpg"
                cv.imwrite(image_path, img)  # Save the frame as an image
                send_msg(text, image_path)
                tTime = cTime

        text = "{}:{}:{} IST".format(hours, minutes, seconds)
        cv.putText(img, str(text), (10, 70), cv.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
        cv.imshow("img", img)

        if cv.waitKey(10) & 0xFF == ord('q'):
            break


if __name__ == "__main__":
    main()
