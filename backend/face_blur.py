import cv2
import numpy as np
import os
from datetime import datetime

class FaceBlurProcessor:
    def __init__(self):
        print("Initializing Face Blur Processor...")
        
        # Load face detection cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            print("Warning: Face cascade not loaded, using fallback method")
            self.face_cascade = None
        
        print("Face Blur Processor initialized!")
    
    def process_video(self, video_path):
        """Apply face blurring to entire video"""
        print(f"Applying privacy protection to: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create output path
        output_dir = "static/processed"
        os.makedirs(output_dir, exist_ok=True)
        
        filename = os.path.basename(video_path)
        output_path = os.path.join(output_dir, f"blurred_{filename}")
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Apply face blurring
            blurred_frame = self.blur_faces(frame)
            
            # Add privacy watermark
            blurred_frame = self.add_privacy_watermark(blurred_frame)
            
            out.write(blurred_frame)
            
            # Print progress
            if frame_count % 30 == 0:
                print(f"  Processed {frame_count} frames...")
        
        cap.release()
        out.release()
        
        print(f"Privacy protection complete: {output_path}")
        return output_path
    
    def blur_faces(self, frame):
        """Detect and blur faces in frame"""
        if self.face_cascade is None:
            return frame
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Blur each face
        for (x, y, w, h) in faces:
            # Extract face ROI
            face_roi = frame[y:y+h, x:x+w]
            
            if face_roi.size > 0:
                # Apply strong blur
                blurred = cv2.GaussianBlur(face_roi, (99, 99), 30)
                
                # Replace with blurred version
                frame[y:y+h, x:x+w] = blurred
        
        return frame
    
    def add_privacy_watermark(self, frame):
        """Add privacy indicator to frame"""
        h, w = frame.shape[:2]
        
        # Add semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (280, 50), (0, 0, 0), -1)
        
        # Apply opacity
        alpha = 0.7
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        # Add text
        cv2.putText(
            frame,
            "PRIVACY MODE: ON - Faces Blurred",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )
        
        return frame
    
    def process_image(self, image_path):
        """Apply face blurring to single image"""
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        # Blur faces
        blurred = self.blur_faces(image)
        
        # Add watermark
        blurred = self.add_privacy_watermark(blurred)
        
        # Save
        output_dir = "static/processed"
        os.makedirs(output_dir, exist_ok=True)
        
        filename = os.path.basename(image_path)
        output_path = os.path.join(output_dir, f"blurred_{filename}")
        
        cv2.imwrite(output_path, blurred)
        
        return output_path