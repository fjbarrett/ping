# api.py
from flask import Flask, jsonify, request

# Assuming your ping functions are in a file named 'ping_functions.py'
from ping.icmp import icmp_ping
from ping.tcp import tcp_ping

app = Flask(__name__)


@app.route("/api/test", methods=["GET"])
def run_test():
    return jsonify({"message": "Test endpoint is working!"})


if __name__ == "__main__":
    # For dev: avoid double-run issues with raw sockets
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)
