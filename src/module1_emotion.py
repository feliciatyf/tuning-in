# Module 1: Emotion Recognition from Video
# This module processes video input to detect and classify human emotions.
# Real-time Facial Emotion Recognition using OpenCV and Deepface
import cv2
from deepface import DeepFace
import pandas as pd
import moviepy.editor as mp
import speech_recognition as sr
from transformers import pipeline
from tqdm import tqdm

# Function to analyze emotions in a video file
def analyze_video_emotions(video_path, output_csv):
    """
    Analyzes emotions frame-by-frame from a video and saves the results to a CSV file.

    Args:
        video_path (str): The path to the video file.
        output_csv (str): The path where the analyzed data will be saved.
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Analyzing video with {frame_count} frames at {frame_rate} FPS...")

    all_emotions = []

    for i in tqdm(range(frame_count)):
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process every nth frame to speed up the analysis
        if i % (frame_rate * 1) == 0:  # Adjust this value to change analysis frequency (e.g., every 1 second)
            
            try:
                # Perform deepface analysis on the frame
                # The actions parameter can be set to ['emotion', 'age', 'gender', 'race']
                results = DeepFace.analyze(img_path=frame, actions=['emotion'], enforce_detection=False)

                # Collect results for each detected face
                for face_result in results:
                    dominant_emotion = face_result['dominant_emotion']
                    emotion_scores = face_result['emotion']
                    all_emotions.append({
                        'frame': i,
                        'timestamp_sec': i / frame_rate,
                        'dominant_emotion': dominant_emotion,
                        **emotion_scores # Unpack all emotion scores
                    })
                # print(f"Frame {i}/{frame_count}: Processed successfully.")

            except Exception as e:
                print(f"Frame {i}: Could not detect face or an error occurred. Skipping. Error: {e}")

    cap.release()
    
    # Save the collected data to a CSV file
    if all_emotions:
        df = pd.DataFrame(all_emotions)
        df.to_csv(output_csv, index=False)
        print(f"Analysis complete. Results saved to {output_csv}")
        emotions_list = ['angry','disgust','fear','happy','sad','surprise','neutral']
        selected_columns_sum=df[emotions_list].sum()
        return selected_columns_sum.idxmax()
    else:
        print("No faces or emotions were detected in the video.")

def analyze_speech_emotions(video_path, audio_path):

    # Load the video
    video = mp.VideoFileClip(video_path)

    # Extract the audio from the video
    audio_file = video.audio
    audio_file.write_audiofile(audio_path)

    # Initialize recognizer
    r = sr.Recognizer()

    # Load the audio file
    with sr.AudioFile(audio_path) as source:
        data = r.record(source)

    # Convert speech to text
    text = r.recognize_google(data)

    # Print the text
    print("\nThe resultant text from video is: \n")
    print(text)

    # Load a pre-trained emotion classification model
    classifier = pipeline("sentiment-analysis", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)

    result = classifier(text)
    print(result)
    return result[0][0]['label'], result[0][0]['score']

# --- Usage Example ---
if __name__ == "__main__":
    # Replace with the path to your video file
    video_file = "test_therapy_video_short.mp4" 
    output_csv_file = "emotion_analysis.csv"
    
    video_emotion = analyze_video_emotions(video_file, output_csv_file)

    print(f"\nDetected video facial emotion: {video_emotion}")

    speech_emotion, confidence = analyze_speech_emotions(video_file, "extracted_audio.wav")

    print(f"\nDetected speech emotion: {speech_emotion} with confidence {confidence:.2f}")
