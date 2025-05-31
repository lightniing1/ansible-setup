from flask import Flask, request, jsonify
import subprocess
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration fetched from environment variables (set by systemd service)
WOL_TARGET_MAC = os.environ.get('WOL_TARGET_MAC')
WOL_BROADCAST_ADDRESS = os.environ.get('WOL_BROADCAST_ADDRESS') # Optional

@app.route('/webhook/wol', methods=['POST'])
def trigger_wol():
    app.logger.info(f"Received request on /webhook/wol from {request.remote_addr}")

    if not WOL_TARGET_MAC:
        app.logger.error("WOL_TARGET_MAC environment variable not set.")
        return jsonify({"status": "error", "message": "Server configuration error: WOL_TARGET_MAC not set"}), 500

    try:
        command = ['wakeonlan']
        
        # Add broadcast address if specified
        if WOL_BROADCAST_ADDRESS:
            command.extend(['-i', WOL_BROADCAST_ADDRESS])
        
        command.append(WOL_TARGET_MAC)
        
        app.logger.info(f"Executing command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=False) # check=False to inspect output

        if result.returncode == 0:
            app.logger.info(f"WoL command successful for {WOL_TARGET_MAC}. Output: {result.stdout.strip()}")
            return jsonify({"status": "success", "message": f"WoL packet sent to {WOL_TARGET_MAC}", "details": result.stdout.strip()}), 200
        else:
            app.logger.error(f"WoL command failed for {WOL_TARGET_MAC}. Return code: {result.returncode}")
            app.logger.error(f"Stderr: {result.stderr.strip()}")
            app.logger.error(f"Stdout: {result.stdout.strip()}")
            return jsonify({"status": "error", 
                            "message": f"Failed to send WoL packet to {WOL_TARGET_MAC}.",
                            "details": result.stderr.strip() or result.stdout.strip()}), 500

    except FileNotFoundError:
        app.logger.error("'wakeonlan' command not found. Is it installed and in PATH?")
        return jsonify({"status": "error", "message": "'wakeonlan' command not found"}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9001)) # Default to 9001 if PORT env var not set
    app.logger.info(f"Starting WoL webhook listener on host 0.0.0.0 port {port}")
    app.run(host='0.0.0.0', port=port)