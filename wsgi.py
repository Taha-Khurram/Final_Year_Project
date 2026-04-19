from app import create_app
from waitress import serve
import logging

app = create_app()

logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    print("🚀 ScriptlyAI is running at http://localhost:5000")
    
    # threads=12: Handles more simultaneous internal tasks
    # connection_limit=100: Prevents the server from hanging on ghost connections
    # channel_timeout=10: Closes idle connections faster to free up resources
    serve(
        app, 
        host='0.0.0.0', 
        port=5000, 
        threads=12, 
        connection_limit=100, 
        channel_timeout=10
    )