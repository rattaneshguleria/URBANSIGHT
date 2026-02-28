from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import eventlet
import os
import json
from datetime import datetime
import threading
import time
import random

eventlet.monkey_patch()

app = Flask(__name__, static_folder='../frontend')
CORS(app, resources={r"/*": {"origins": "*"}})

# Add CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   async_mode='eventlet',
                   path='socket.io',
                   ping_timeout=60,
                   ping_interval=25)

# Import AI modules
from detector import VideoAnalyzer
from face_blur import FaceBlurProcessor

# Initialize modules
analyzer = VideoAnalyzer()
face_processor = FaceBlurProcessor()

# Create necessary directories
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("static/processed", exist_ok=True)

# Store analysis results
analyses = {}
alerts_history = []

# ============================================
# FRONTEND ROUTES
# ============================================

@app.route('/')
def serve_dashboard():
    """Serve the main dashboard page"""
    return send_from_directory('../frontend', 'dashboard.html')

@app.route('/<path:path>')
def serve_static_files(path):
    """Serve all static frontend files (CSS, JS, HTML)"""
    return send_from_directory('../frontend', path)

@app.route('/static/<path:filename>')
def serve_processed_files(filename):
    """Serve processed videos and images"""
    return send_from_directory('static', filename)

@app.route('/uploads/<path:filename>')
def serve_uploaded_files(filename):
    """Serve uploaded videos"""
    return send_from_directory('uploads', filename)

# ============================================
# API ROUTES - DASHBOARD DATA
# ============================================

@app.route('/api/status', methods=['GET'])
def system_status():
    """Get overall system status for dashboard"""
    return jsonify({
        'status': 'operational',
        'analyses_count': len(analyses),
        'alerts_count': len(alerts_history),
        'active_features': [
            'crowd_detection',
            'suspicious_activity',
            'unattended_objects',
            'privacy_mode',
            'real_time_alerts'
        ],
        'model_status': analyzer.get_model_status() if hasattr(analyzer, 'get_model_status') else {
            'status': 'operational',
            'model': 'OpenCV HOG',
            'features': ['crowd_detection', 'violence_detection']
        }
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    today = datetime.now().date()
    today_alerts = []
    
    for a in alerts_history:
        try:
            if datetime.fromisoformat(a['timestamp']).date() == today:
                today_alerts.append(a)
        except:
            pass
    
    return jsonify({
        'total_analyses': len(analyses),
        'total_alerts': len(alerts_history),
        'today_alerts': len(today_alerts),
        'active_cameras': 0,  # Will be updated when cameras are active
        'by_severity': {
            'high': len([a for a in alerts_history if a.get('severity') == 'high']),
            'medium': len([a for a in alerts_history if a.get('severity') == 'medium']),
            'low': len([a for a in alerts_history if a.get('severity') == 'low'])
        },
        'by_type': {
            'crowd': len([a for a in alerts_history if 'crowd' in a.get('type', '').lower()]),
            'violence': len([a for a in alerts_history if 'violence' in a.get('type', '').lower()]),
            'object': len([a for a in alerts_history if 'object' in a.get('type', '').lower()])
        }
    })

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts for dashboard"""
    limit = request.args.get('limit', 10, type=int)
    return jsonify({
        'total': len(alerts_history),
        'alerts': alerts_history[-limit:][::-1]  # Most recent first
    })

@app.route('/api/activity', methods=['GET'])
def get_recent_activity():
    """Get recent activity for dashboard"""
    limit = request.args.get('limit', 10, type=int)
    activities = []
    
    for alert in alerts_history[-limit:][::-1]:
        activities.append({
            'type': alert.get('type', 'alert'),
            'message': alert.get('message', 'Activity detected'),
            'timestamp': alert.get('timestamp', datetime.now().isoformat()),
            'severity': alert.get('severity', 'medium')
        })
    
    return jsonify(activities)

# ============================================
# VIDEO ANALYSIS ROUTES
# ============================================

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_video():
    """Upload and analyze video file"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file'}), 400
        
        video = request.files['video']
        if video.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Save video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{video.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        video.save(filepath)
        
        # Process video with AI
        result = analyzer.analyze_video(filepath)
        
        # Add face blurring for privacy
        privacy_mode = request.form.get('privacy_mode', 'true')
        if privacy_mode.lower() == 'true':
            blurred_path = face_processor.process_video(filepath)
            if blurred_path:
                relative_path = os.path.basename(blurred_path)
                result['processed_video'] = f"/static/processed/{relative_path}"
        
        # Store result
        result_id = f"analysis_{timestamp}"
        analyses[result_id] = result
        
        # Add alerts for suspicious activity
        if result.get('alerts'):
            for alert_data in result.get('alerts', []):
                alert = {
                    'id': len(alerts_history) + 1,
                    'type': alert_data.get('type', 'unknown'),
                    'message': alert_data.get('message', 'Suspicious activity detected'),
                    'timestamp': datetime.now().isoformat(),
                    'severity': alert_data.get('severity', 'medium'),
                    'video_id': result_id
                }
                alerts_history.append(alert)
                
                # Send real-time alert via WebSocket
                socketio.emit('alert', alert)
        
        # Send analysis complete notification
        socketio.emit('analysis_complete', {
            'result_id': result_id,
            'summary': result.get('summary', {})
        })
        
        return jsonify({
            'success': True,
            'result_id': result_id,
            'summary': result.get('summary', {}),
            'alerts': result.get('alerts', [])
        })
        
    except Exception as e:
        print(f"Error in upload_video: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/demo/analyze', methods=['POST'])
def demo_analysis():
    """Run demo analysis for testing"""
    try:
        # Generate demo analysis results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_id = f"demo_{timestamp}"
        
        # Create demo alerts
        demo_alerts = [
            {
                'type': 'crowd',
                'message': 'Moderate crowd detected in main area',
                'severity': 'low',
                'frame': 150,
                'timestamp': 15.5
            },
            {
                'type': 'object',
                'message': 'Unattended backpack detected',
                'severity': 'medium',
                'frame': 320,
                'timestamp': 32.0
            }
        ]
        
        # Create demo summary
        demo_summary = {
            'total_frames': 450,
            'max_people': 8,
            'avg_people': 3.2,
            'total_alerts': 2,
            'alert_types': {'crowd': 1, 'object': 1},
            'timeline': [
                {'time': 0, 'people': 2, 'density': 0.1},
                {'time': 10, 'people': 5, 'density': 0.25},
                {'time': 20, 'people': 8, 'density': 0.4},
                {'time': 30, 'people': 6, 'density': 0.3},
                {'time': 40, 'people': 3, 'density': 0.15}
            ],
            'description': 'Demo analysis completed successfully.'
        }
        
        # Store demo results
        analyses[result_id] = {
            'summary': demo_summary,
            'alerts': demo_alerts,
            'suspicious_activity': demo_alerts[0] if demo_alerts else None
        }
        
        # Add alerts to history
        for alert_data in demo_alerts:
            alert = {
                'id': len(alerts_history) + 1,
                'type': alert_data['type'],
                'message': alert_data['message'],
                'timestamp': datetime.now().isoformat(),
                'severity': alert_data['severity'],
                'video_id': result_id,
                'simulated': True
            }
            alerts_history.append(alert)
            socketio.emit('alert', alert)
        
        return jsonify({
            'success': True,
            'result_id': result_id,
            'summary': demo_summary,
            'alerts': demo_alerts
        })
        
    except Exception as e:
        print(f"Error in demo_analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================
# PRIVACY MODE ROUTES
# ============================================

@app.route('/api/privacy/toggle', methods=['POST'])
def toggle_privacy_mode():
    """Toggle privacy mode setting"""
    try:
        data = request.json
        enabled = data.get('enabled', True)
        
        # Store privacy setting (you can save to config file)
        with open('privacy_config.json', 'w') as f:
            json.dump({'privacy_mode': enabled}, f)
        
        return jsonify({
            'success': True,
            'privacy_mode': enabled,
            'message': f'Privacy mode {"enabled" if enabled else "disabled"}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/privacy/status', methods=['GET'])
def privacy_status():
    """Get current privacy mode status"""
    try:
        if os.path.exists('privacy_config.json'):
            with open('privacy_config.json', 'r') as f:
                config = json.load(f)
                enabled = config.get('privacy_mode', True)
        else:
            enabled = True
        
        return jsonify({
            'privacy_mode': enabled,
            'face_blurring': 'enabled' if enabled else 'disabled'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# WEBSOCKET EVENTS
# ============================================

@socketio.on('connect')
def handle_connect():
    """Handle client WebSocket connection"""
    print(f'Client connected: {request.sid}')
    emit('connected', {
        'message': 'Connected to UrbanSight AI System',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client WebSocket disconnection"""
    print(f'Client disconnected: {request.sid}')

@socketio.on('request_alerts')
def handle_request_alerts():
    """Send recent alerts to newly connected client"""
    recent_alerts = alerts_history[-10:][::-1]
    emit('initial_alerts', {'alerts': recent_alerts})

# ============================================
# LIVE MONITORING SIMULATION
# ============================================

def simulate_live_monitoring():
    """Simulate live camera feed for demo"""
    while True:
        time.sleep(45)  # Generate alert every 45 seconds
        
        try:
            # 40% chance to generate alert
            if random.random() > 0.6:
                alert_types = [
                    ('crowd', 'Sudden crowd increase at entrance', 'medium'),
                    ('crowd', 'High density in main lobby', 'high'),
                    ('violence', 'Suspicious movement detected', 'medium'),
                    ('object', 'Unattended bag in corridor', 'medium'),
                    ('crowd', 'Moderate crowd near elevator', 'low'),
                    ('violence', 'Rapid movement in parking lot', 'high')
                ]
                
                alert_type, message, severity = random.choice(alert_types)
                
                alert = {
                    'id': len(alerts_history) + 1,
                    'type': alert_type,
                    'message': message,
                    'timestamp': datetime.now().isoformat(),
                    'severity': severity,
                    'simulated': True
                }
                
                alerts_history.append(alert)
                socketio.emit('alert', alert)
                print(f"Simulated alert: {message}")
                
        except Exception as e:
            print(f"Error in simulation: {e}")
            continue

# ============================================
# CHART DATA ROUTES
# ============================================

@app.route('/api/charts/crowd', methods=['GET'])
def get_crowd_chart_data():
    """Get crowd density trend data for charts"""
    # Generate sample data for the last 10 time periods
    labels = []
    data = []
    
    for i in range(10, 0, -1):
        time_label = f"{(datetime.now().hour - i) % 24}:00"
        labels.append(time_label)
        
        # Generate realistic crowd data
        base_value = 15
        variation = random.randint(-5, 10)
        data.append(max(0, base_value + variation))
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'People Count',
            'data': data,
            'borderColor': '#00d4ff',
            'backgroundColor': 'rgba(0, 212, 255, 0.1)'
        }]
    })

@app.route('/api/charts/alerts', methods=['GET'])
def get_alert_chart_data():
    """Get alert distribution data for charts"""
    crowd_count = len([a for a in alerts_history if 'crowd' in a.get('type', '').lower()])
    violence_count = len([a for a in alerts_history if 'violence' in a.get('type', '').lower()])
    object_count = len([a for a in alerts_history if 'object' in a.get('type', '').lower()])
    
    # Ensure we have some data to display
    if crowd_count + violence_count + object_count == 0:
        crowd_count, violence_count, object_count = 12, 5, 3
    
    return jsonify({
        'labels': ['Crowd', 'Violence', 'Object'],
        'datasets': [{
            'data': [crowd_count, violence_count, object_count],
            'backgroundColor': ['#00d4ff', '#ff4757', '#2ed573']
        }]
    })

@app.route('/api/charts/timeline', methods=['GET'])
def get_timeline_chart_data():
    """Get activity timeline data for charts"""
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    data = []
    
    for i in range(7):
        # Generate realistic alert counts
        if i < 5:  # Weekdays
            data.append(random.randint(3, 10))
        else:  # Weekend
            data.append(random.randint(1, 6))
    
    return jsonify({
        'labels': days,
        'datasets': [{
            'label': 'Alerts',
            'data': data,
            'backgroundColor': '#00d4ff'
        }]
    })

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == '__main__':
    # Start live monitoring thread
    monitor_thread = threading.Thread(target=simulate_live_monitoring, daemon=True)
    monitor_thread.start()
    
    # Print startup banner
    print("="*60)
    print("  UrbanSight AI Surveillance System")
    print("="*60)
    print(f"  Dashboard: http://localhost:5000")
    print(f"  API: http://localhost:5000/api/status")
    print(f"  WebSocket: ws://localhost:5000/socket.io")
    print("="*60)
    print("  Active Features:")
    print("  • Crowd Detection")
    print("  • Suspicious Activity Detection")
    print("  • Unattended Object Detection")
    print("  • Privacy Mode (Face Blurring)")
    print("  • Real-time Alerts")
    print("="*60)
    print("  Server starting... Press Ctrl+C to stop")
    print("="*60)
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)