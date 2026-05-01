from app import create_app
from waitress import serve
import logging
import os

app = create_app()

logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'

    if debug:
        print("🔧 ScriptlyAI running in DEBUG mode at http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("🚀 ScriptlyAI is running at http://localhost:5000")
        serve(
            app,
            host='0.0.0.0',
            port=5000,
            threads=12,
            connection_limit=100,
            channel_timeout=10
        )