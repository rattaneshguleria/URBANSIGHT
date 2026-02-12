// Global variables
let socket = null;
let currentAnalysis = null;
let charts = {};

// Initialize dashboard
async function loadDashboardData() {
    try {
        // Load system status
        const statusResponse = await fetch('/api/status');
        const statusData = await statusResponse.json();
        
        // Update status display
        document.getElementById('activeCameras').textContent = 
            statusData.analyses_count || 0;
        
        // Load stats
        const statsResponse = await fetch('/api/stats');
        const statsData = await statsResponse.json();
        
        document.getElementById('todayAlerts').textContent = statsData.today_alerts;
        document.getElementById('totalAnalyses').textContent = statsData.total_analyses;
        
        // Load alerts
        await loadAlerts();
        
        // Load recent activity
        await loadRecentActivity();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Initialize charts
function initializeCharts() {
    // Crowd Chart
    const crowdCtx = document.getElementById('crowdChart').getContext('2d');
    charts.crowd = new Chart(crowdCtx, {
        type: 'line',
        data: {
            labels: Array.from({length: 10}, (_, i) => `${i * 10}:00`),
            datasets: [{
                label: 'People Count',
                data: [5, 8, 12, 15, 20, 18, 14, 10, 8, 6],
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0, 212, 255, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: 'rgba(255, 255, 255, 0.8)' }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: 'rgba(255, 255, 255, 0.6)' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: 'rgba(255, 255, 255, 0.6)' }
                }
            }
        }
    });
    
    // Alert Distribution Chart
    const alertCtx = document.getElementById('alertChart').getContext('2d');
    charts.alert = new Chart(alertCtx, {
        type: 'doughnut',
        data: {
            labels: ['Crowd', 'Violence', 'Object'],
            datasets: [{
                data: [12, 5, 3],
                backgroundColor: ['#00d4ff', '#ff4757', '#2ed573']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: 'rgba(255, 255, 255, 0.8)' }
                }
            }
        }
    });
    
    // Timeline Chart
    const timelineCtx = document.getElementById('timelineChart').getContext('2d');
    charts.timeline = new Chart(timelineCtx, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Alerts',
                data: [3, 5, 2, 8, 4, 6, 3],
                backgroundColor: '#00d4ff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: 'rgba(255, 255, 255, 0.8)' }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: 'rgba(255, 255, 255, 0.6)' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: 'rgba(255, 255, 255, 0.6)' }
                }
            }
        }
    });
}

// Setup WebSocket connection
function setupWebSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to WebSocket');
        updateStatusIndicator(true);
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from WebSocket');
        updateStatusIndicator(false);
    });
    
    socket.on('alert', function(alert) {
        console.log('New alert received:', alert);
        addAlertToDashboard(alert);
        showAlertNotification(alert);
    });
    
    socket.on('analysis_complete', function(data) {
        console.log('Analysis complete:', data);
        if (currentAnalysis && currentAnalysis.result_id === data.result_id) {
            showAnalysisResults(data);
        }
    });
}

function updateStatusIndicator(isConnected) {
    const statusDot = document.querySelector('.status-dot');
    if (isConnected) {
        statusDot.classList.add('active');
    } else {
        statusDot.classList.remove('active');
    }
}

// Load alerts
async function loadAlerts() {
    try {
        const response = await fetch('/api/alerts?limit=5');
        const raw = await response.text();
console.log("RAW RESPONSE:", raw);

if (!raw) {
    throw new Error("Empty response from backend");
}

const data = JSON.parse(raw);

        
        const container = document.getElementById('alertsContainer');
        
        if (data.alerts.length === 0) {
            container.innerHTML = `
                <div class="alert-placeholder">
                    <i class="fas fa-check-circle"></i>
                    <p>No active alerts. System is monitoring.</p>
                </div>
            `;
            return;
        }
        
        let alertsHTML = '';
        data.alerts.forEach(alert => {
            const time = new Date(alert.timestamp).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            alertsHTML += `
                <div class="alert-item ${alert.type}">
                    <div class="alert-header">
                        <div class="alert-type">
                            <i class="fas fa-${getAlertIcon(alert.type)}"></i>
                            ${getAlertTitle(alert.type)}
                        </div>
                        <div class="alert-time">${time}</div>
                    </div>
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-severity severity-${alert.severity}">
                        ${alert.severity.toUpperCase()}
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = alertsHTML;
        
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

function getAlertIcon(type) {
    const icons = {
        'crowd': 'users',
        'violence': 'running',
        'object': 'suitcase'
    };
    return icons[type] || 'exclamation-triangle';
}

function getAlertTitle(type) {
    const titles = {
        'crowd': 'Crowd Alert',
        'violence': 'Suspicious Activity',
        'object': 'Unattended Object'
    };
    return titles[type] || 'Alert';
}

// Add new alert to dashboard
function addAlertToDashboard(alert) {
    const container = document.getElementById('alertsContainer');
    const placeholder = container.querySelector('.alert-placeholder');
    
    if (placeholder) {
        container.innerHTML = '';
    }
    
    const time = new Date(alert.timestamp).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    const alertHTML = `
        <div class="alert-item ${alert.type}">
            <div class="alert-header">
                <div class="alert-type">
                    <i class="fas fa-${getAlertIcon(alert.type)}"></i>
                    ${getAlertTitle(alert.type)}
                </div>
                <div class="alert-time">${time}</div>
            </div>
            <div class="alert-message">${alert.message}</div>
            <div class="alert-severity severity-${alert.severity}">
                ${alert.severity.toUpperCase()}
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('afterbegin', alertHTML);
    
    // Update charts
    updateChartsWithAlert(alert);
}

function updateChartsWithAlert(alert) {
    if (!charts.alert || !charts.timeline) return;
    
    // Update alert distribution chart
    const alertIndex = ['crowd', 'violence', 'object'].indexOf(alert.type);
    if (alertIndex !== -1) {
        charts.alert.data.datasets[0].data[alertIndex]++;
        charts.alert.update();
    }
    
    // Update timeline chart (simplified)
    const today = new Date().getDay();
    charts.timeline.data.datasets[0].data[today]++;
    charts.timeline.update();
}

// Show alert notification
function showAlertNotification(alert) {
    if (!("Notification" in window)) return;
    
    if (Notification.permission === "granted") {
        new Notification(`UrbanSight Alert: ${getAlertTitle(alert.type)}`, {
            body: alert.message,
            icon: '/favicon.ico'
        });
    } else if (Notification.permission !== "denied") {
        Notification.requestPermission();
    }
}

// Load recent activity
async function loadRecentActivity() {
    try {
        const response = await fetch('/api/alerts?limit=10');
        const data = await response.json();
        
        const container = document.getElementById('activityList');
        let activityHTML = '';
        
        data.alerts.forEach(alert => {
            const time = new Date(alert.timestamp).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            const date = new Date(alert.timestamp).toLocaleDateString();
            
            activityHTML += `
                <div class="activity-item">
                    <div class="activity-content">
                        <strong>${getAlertTitle(alert.type)}</strong>
                        <small>${alert.message}</small>
                    </div>
                    <div class="activity-time">${date} ${time}</div>
                </div>
            `;
        });
        
        container.innerHTML = activityHTML;
        
    } catch (error) {
        console.error('Error loading activity:', error);
    }
}

// Video analysis
async function analyzeVideo() {
    const videoInput = document.getElementById('videoInput');
    const privacyMode = document.getElementById('privacyMode').checked;
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsContainer = document.getElementById('resultsContainer');
    const progressContainer = document.getElementById('progressContainer');
    const alertSummary = document.getElementById('alertSummary');
    
    if (!videoInput.files.length) {
        alert('Please select a video file first');
        return;
    }
    
    // Show progress
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    
    resultsContainer.innerHTML = `
        <div class="results-placeholder">
            <i class="fas fa-spinner fa-spin"></i>
            <h4>Processing Video</h4>
            <p>AI analysis in progress...</p>
        </div>
    `;
    
    progressContainer.style.display = 'block';
    alertSummary.style.display = 'none';
    
    // Update progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 10;
        if (progress > 90) progress = 90;
        
        document.getElementById('progressFill').style.width = progress + '%';
        document.getElementById('progressText').textContent = progress + '%';
        
        const stages = [
            'Uploading video...',
            'Initializing AI models...',
            'Extracting frames...',
            'Detecting objects...',
            'Analyzing movement...',
            'Checking for alerts...',
            'Finalizing results...'
        ];
        
        const stageIndex = Math.floor(progress / 15);
        if (stageIndex < stages.length) {
            document.getElementById('progressDetails').textContent = stages[stageIndex];
        }
    }, 500);
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('video', videoInput.files[0]);
        formData.append('privacy_mode', privacyMode);
        
        // Send to backend
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        
        // Complete progress
        document.getElementById('progressFill').style.width = '100%';
        document.getElementById('progressText').textContent = '100%';
        document.getElementById('progressDetails').textContent = 'Analysis complete!';
        
        const data = await response.json();
        
        if (data.success) {
            currentAnalysis = data;
            showAnalysisResults(data);
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
        
    } catch (error) {
        console.error('Error analyzing video:', error);
        
        resultsContainer.innerHTML = `
            <div class="results-placeholder error">
                <i class="fas fa-exclamation-circle"></i>
                <h4>Analysis Failed</h4>
                <p>${error.message}</p>
            </div>
        `;
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-play"></i> Start AI Analysis';
        
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 2000);
    }
}

function showAnalysisResults(data) {
    const resultsContainer = document.getElementById('resultsContainer');
    const alertSummary = document.getElementById('alertSummary');
    
    let resultsHTML = `
        <div class="analysis-results">
            <div class="result-header success">
                <i class="fas fa-check-circle"></i>
                <h4>Analysis Complete</h4>
            </div>
            
            <div class="result-summary">
                <div class="summary-stat">
                    <i class="fas fa-clock"></i>
                    <div>
                        <span class="stat-value">${data.summary.total_frames || 0}</span>
                        <span class="stat-label">Frames Analyzed</span>
                    </div>
                </div>
                
                <div class="summary-stat">
                    <i class="fas fa-users"></i>
                    <div>
                        <span class="stat-value">${data.summary.max_people || 0}</span>
                        <span class="stat-label">Max People</span>
                    </div>
                </div>
                
                <div class="summary-stat">
                    <i class="fas fa-bell"></i>
                    <div>
                        <span class="stat-value">${data.summary.total_alerts || 0}</span>
                        <span class="stat-label">Alerts Found</span>
                    </div>
                </div>
            </div>
            
            <div class="result-details">
                <h5>Analysis Summary</h5>
                <p>${data.summary.description || 'Video analysis completed successfully.'}</p>
            </div>
        </div>
    `;
    
    resultsContainer.innerHTML = resultsHTML;
    
    // Show alert summary if any alerts
    if (data.alerts && data.alerts.length > 0) {
        let alertHTML = `
            <div class="alert-summary-header">
                <i class="fas fa-exclamation-triangle"></i>
                <h4>Detected Alerts</h4>
            </div>
        `;
        
        data.alerts.forEach(alert => {
            alertHTML += `
                <div class="summary-item ${alert.type}">
                    <div class="summary-header">
                        <div class="summary-title">
                            <i class="fas fa-${getAlertIcon(alert.type)}"></i>
                            ${getAlertTitle(alert.type)}
                        </div>
                        <div class="summary-count">${alert.severity.toUpperCase()}</div>
                    </div>
                    <div class="summary-details">${alert.message}</div>
                </div>
            `;
        });
        
        alertSummary.innerHTML = alertHTML;
        alertSummary.style.display = 'block';
    }
}

// Demo functions
function runDemoAnalysis() {
    // Simulate a demo analysis
    const demoData = {
        success: true,
        summary: {
            total_frames: 450,
            max_people: 8,
            avg_people: 3.2,
            total_alerts: 2,
            description: 'Demo analysis detected normal crowd levels with 2 minor alerts.'
        },
        alerts: [
            {
                type: 'crowd',
                message: 'Moderate crowd detected in area A',
                severity: 'low',
                timestamp: new Date().toISOString()
            },
            {
                type: 'object',
                message: 'Unattended backpack detected',
                severity: 'medium',
                timestamp: new Date().toISOString()
            }
        ]
    };
    
    showAnalysisResults(demoData);
    
    // Show notification
    showAlertNotification(demoData.alerts[0]);
}

function togglePrivacyMode() {
    const privacyBtn = document.querySelector('.btn.action-btn:nth-child(3)');
    const isEnabled = privacyBtn.textContent.includes('Disable');
    
    if (isEnabled) {
        privacyBtn.innerHTML = '<i class="fas fa-user-shield"></i> Enable Privacy Mode';
        showNotification('Privacy Mode Disabled', 'Faces will not be blurred');
    } else {
        privacyBtn.innerHTML = '<i class="fas fa-user-shield"></i> Disable Privacy Mode';
        showNotification('Privacy Mode Enabled', 'Faces will be automatically blurred');
    }
}

function viewAllAlerts() {
    window.location.href = 'upload.html?view=alerts';
}

function refreshAlerts() {
    loadAlerts();
    showNotification('Alerts Refreshed', 'Updated alert list from server');
}

function showNotification(title, message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-info-circle"></i>
            <div>
                <strong>${title}</strong>
                <p>${message}</p>
            </div>
            <button class="btn-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(16, 20, 31, 0.95);
        border: 1px solid #00d4ff;
        border-radius: 10px;
        padding: 15px;
        min-width: 300px;
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Start live updates
function startLiveUpdates() {
    // Update dashboard every 30 seconds
    setInterval(() => {
        loadDashboardData();
    }, 30000);
    
    // Simulate occasional alerts for demo
    if (window.location.href.includes('index.html')) {
        setInterval(() => {
            // 10% chance to simulate an alert
            if (Math.random() < 0.1) {
                const alertTypes = [
                    { type: 'crowd', message: 'Crowd density increasing in main area', severity: 'low' },
                    { type: 'violence', message: 'Suspicious movement detected', severity: 'medium' },
                    { type: 'object', message: 'Unattended item spotted', severity: 'medium' }
                ];
                
                const alert = alertTypes[Math.floor(Math.random() * alertTypes.length)];
                alert.timestamp = new Date().toISOString();
                
                addAlertToDashboard(alert);
            }
        }, 60000); // Every minute
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        if (window.location.pathname.includes('index.html') || 
            window.location.pathname === '/') {
            loadDashboardData();
            initializeCharts();
            setupWebSocket();
            startLiveUpdates();
        }
    });
} else {
    if (window.location.pathname.includes('index.html') || 
        window.location.pathname === '/') {
        loadDashboardData();
        initializeCharts();
        setupWebSocket();
        startLiveUpdates();
    }
}