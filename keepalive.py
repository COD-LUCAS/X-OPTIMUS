import os
import time
import threading
import requests
import logging
from flask import Flask, jsonify
from datetime import datetime

logger = logging.getLogger(__name__)

START_TIME = time.time()

app = Flask('X-OPTIMUS-KEEPALIVE')

@app.route('/')
def home():
    uptime = int(time.time() - START_TIME)
    return jsonify({
        'status': 'online',
        'bot': 'X-OPTIMUS',
        'uptime_seconds': uptime,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/stats')
def stats():
    uptime = int(time.time() - START_TIME)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    seconds = uptime % 60
    return jsonify({
        'uptime': f'{hours}h {minutes}m {seconds}s',
        'timestamp': datetime.now().isoformat()
    })

def keep_alive():
    """Start Flask server on port 8000"""
    port = int(os.getenv('PORT', 8000))
    logger.info(f'Starting keepalive server on port {port}')
    
    app.run(
        host='0.0.0.0',
        port=port,
        threaded=True,
        debug=False
    )

def start_keepalive_thread():
    """Start keepalive in a daemon thread"""
    t = threading.Thread(target=keep_alive, daemon=True)
    t.start()
    logger.info('Keepalive thread started')

def auto_ping_self():
    """Periodically ping self to prevent Koyeb sleep"""
    url = os.getenv('KOYEB_URL')
    
    if not url:
        logger.warning('KOYEB_URL not set - auto-ping disabled')
        return
    
    logger.info(f'Auto-ping enabled for: {url}')
    
    while True:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.debug('Auto-ping successful')
            else:
                logger.warning(f'Auto-ping returned {response.status_code}')
        except Exception as e:
            logger.error(f'Auto-ping failed: {e}')
        
        time.sleep(300)  # Ping every 5 minutes

def start_autopinger_thread():
    """Start auto-pinger in a daemon thread"""
    t = threading.Thread(target=auto_ping_self, daemon=True)
    t.start()
    logger.info('Auto-pinger thread started')
