import streamlit as st
from datetime import datetime
import pytz
import time
from ultralytics import YOLO
import cv2 as cv
import requests

# Function to check if the current time is within a specified time range
def is_current_time_within_limits(from_time, to_time):
    try:
        current_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        from_time_obj = datetime.strptime(from_time, '%H:%M:%S').time()
        to_time_obj = datetime.strptime(to_time, '%H:%M:%S').time()
        return from_time_obj <= current_time <= to_time_obj
    except ValueError:
        st.error("Invalid time format. Please use HH:MM:SS.")
        return False

# Function to perform object detection and surveillance
def perform_surveillance(input_type, source, token, chat_id, from_time, to_time):
    model = YOLO('yolov8n.pt')  # Update the YOLO model filename here

    if input_type == 'Camera':
        cap = cv.VideoCapture(source)
    else:
        cap = cv.VideoCapture(source)

    if not cap.isOpened():
        st.error("Error: Unable to open video source.")
        return

    fps_interval = 5  # seconds
    last_fps_display_time = time.time()

    while True:
        if is_current_time_within_limits(from_time, to_time):
            ret, img = cap.read()
            if not ret:
                st.error("Error reading video feed.")
                break

            # Perform object detection using YOLO
            results = model.predict(img, conf=0.6)

            # Process detection results
            person_detected = False
            for detection in results[0]:
                if int(detection.boxes.cls) == 0:
                    person_detected = True
                    detection = detection.boxes.xyxy
                    x1, y1, x2, y2 = detection[0]

                    # Draw bounding box and label
                    cv.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    cv.putText(img, "Person", (int(x1), int(y1)), cv.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

            # Display FPS at an interval of 10 seconds
            if time.time() - last_fps_display_time >= fps_interval:
                cTime = time.time()
                fps = 1 / (cTime - pTime) if 'pTime' in locals() else 0
                pTime = cTime
                st.write(f"FPS: {int(fps)}")
                last_fps_display_time = time.time()

            # Display the processed image if a person is detected
            if person_detected:
                st.image(img, channels="BGR")

                # Add current time overlay on the image
                current_time = datetime.now().strftime('%H:%M:%S')
                img_with_time = add_timestamp(img, current_time)

                # Send image to Telegram
                send_telegram_message(token, chat_id, img_with_time)

    # Release the video capture object
    cap.release()

# Function to add timestamp on image
def add_timestamp(img, current_time):
    height, width, _ = img.shape
    cv.putText(img, f"Time: {current_time}", (10, height - 10), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return img

# Function to send image message to Telegram
def send_telegram_message(token, chat_id, img):
    try:
        url_req = f"https://api.telegram.org/bot{token}/sendPhoto"
        _, img_encoded = cv.imencode('.jpg', img)
        files = {'photo': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')}
        data = {'chat_id': chat_id, 'caption': "Person detected!"}
        response = requests.post(url_req, data=data, files=files)
        if response.status_code != 200:
            st.warning("Failed to send message to Telegram.")
    except Exception as e:
        st.error(f"Error sending message to Telegram: {e}")

def main():
    st.markdown("""
        <div style="display: flex; justify-content: center;">
            <img src="https://cdn.vectorstock.com/i/1000x1000/34/79/surveillance-logo-design-template-vector-20643479.webp" alt="Logo" width="100">
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>AUTOMATOS- Automatic Surveillance System</h1>", unsafe_allow_html=True)

    # Streamlit widgets for user input
    input_type = st.radio("Select input type:", ('Camera', 'Video File'))
    if input_type == 'Camera':
        source = st.radio("Select camera source:", (0, 1))  # Use 0 for default camera
    else:
        source = st.file_uploader("Upload a video file:", type=['mp4', 'avi', 'mkv'])

    token = st.text_input("Enter your Telegram bot token:")
    chat_id = st.text_input("Enter your Telegram chat ID:")
    from_time = st.time_input("Select start time:")
    to_time = st.time_input("Select end time:")

    status_placeholder = st.empty()

    if st.button("Start Surveillance"):
        status_placeholder.text("Surveillance started...")
        if input_type == 'Camera':
            perform_surveillance('Camera', int(source), token, chat_id, from_time.strftime('%H:%M:%S'), to_time.strftime('%H:%M:%S'))
        else:
            if source is not None:
                perform_surveillance('Video File', source.name, token, chat_id, from_time.strftime('%H:%M:%S'), to_time.strftime('%H:%M:%S'))
            else:
                st.error("Please upload a video file.")

if __name__ == '__main__':
    main()

