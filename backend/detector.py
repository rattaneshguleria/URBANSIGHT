import cv2
import numpy as np
from collections import defaultdict, deque
from datetime import datetime
import os

class VideoAnalyzer:
    def __init__(self):
        print("Initializing Video Analyzer...")
        
        # Detection thresholds
        self.crowd_threshold = 8
        self.violence_threshold = 50  # Pixel movement threshold
        self.object_time_threshold = 5  # seconds
        
        # Tracking variables
        self.person_tracks = defaultdict(list)
        self.frame_count = 0
        
        # Load HOG descriptor for people detection
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        print("Video Analyzer initialized successfully!")
    
    def analyze_video(self, video_path):
        """Analyze video for suspicious activities"""
        print(f"Analyzing video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Could not open video"}
        
        # Video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Analysis results
        results = {
            'video_info': {
                'fps': fps,
                'total_frames': total_frames,
                'duration': total_frames / fps if fps > 0 else 0
            },
            'alerts': [],
            'summary': {}
        }
        
        frame_number = 0
        prev_positions = {}
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_number += 1
            
            # Process every 5th frame for speed
            if frame_number % 5 != 0:
                continue
            
            # Analyze frame
            people_count, positions, movement_scores = self.analyze_frame(frame, prev_positions)
            
            # Check for alerts
            alerts = self.check_alerts(people_count, movement_scores, frame_number, fps)
            if alerts:
                results['alerts'].extend(alerts)
            
            # Update previous positions
            prev_positions = positions
        
        cap.release()
        
        # Generate summary
        results['summary'] = self.generate_summary(results)
        
        return results
    
    def analyze_frame(self, frame, prev_positions=None):
        """Detect people and analyze movement"""
        # Detect people using HOG
        (rects, _) = self.hog.detectMultiScale(
            frame,
            winStride=(4, 4),
            padding=(8, 8),
            scale=1.05
        )
        
        people_count = len(rects)
        positions = {}
        movement_scores = {}
        
        # Process each detected person
        for i, (x, y, w, h) in enumerate(rects):
            # Filter small detections
            if w * h < 2000:
                continue
                
            # Calculate center point
            center_x = x + w // 2
            center_y = y + h // 2
            positions[i] = (center_x, center_y)
            
            # Calculate movement
            if prev_positions and i in prev_positions:
                prev_x, prev_y = prev_positions[i]
                movement = np.sqrt((center_x - prev_x)**2 + (center_y - prev_y)**2)
                movement_scores[i] = movement
        
        return people_count, positions, movement_scores
    
    def check_alerts(self, people_count, movement_scores, frame_number, fps):
        """Generate alerts based on analysis"""
        alerts = []
        
        # Crowd alert
        if people_count > self.crowd_threshold:
            severity = 'high' if people_count > 15 else 'medium'
            alerts.append({
                'type': 'crowd',
                'message': f'Large crowd detected: {people_count} people',
                'severity': severity,
                'frame': frame_number,
                'timestamp': frame_number / fps if fps > 0 else 0
            })
        elif people_count > 5:
            alerts.append({
                'type': 'crowd',
                'message': f'Moderate crowd: {people_count} people',
                'severity': 'low',
                'frame': frame_number,
                'timestamp': frame_number / fps if fps > 0 else 0
            })
        
        # Suspicious movement alert
        if movement_scores:
            avg_movement = np.mean(list(movement_scores.values()))
            if avg_movement > self.violence_threshold:
                alerts.append({
                    'type': 'violence',
                    'message': 'Suspicious rapid movement detected',
                    'severity': 'medium',
                    'frame': frame_number,
                    'timestamp': frame_number / fps if fps > 0 else 0
                })
        
        return alerts
    
    def generate_summary(self, results):
        """Generate analysis summary"""
        total_alerts = len(results['alerts'])
        alert_types = {}
        
        for alert in results['alerts']:
            alert_type = alert['type']
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
        
        return {
            'total_frames': results['video_info']['total_frames'],
            'duration': round(results['video_info']['duration'], 2),
            'total_alerts': total_alerts,
            'alert_types': alert_types,
            'description': f'Analysis complete. Detected {total_alerts} incidents.'
        }
    
    def get_model_status(self):
        """Get model status for dashboard"""
        return {
            'status': 'operational',
            'model': 'OpenCV HOG',
            'features': ['crowd_detection', 'violence_detection'],
            'thresholds': {
                'crowd': self.crowd_threshold,
                'violence': self.violence_threshold
            }
        }