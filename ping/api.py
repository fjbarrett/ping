# api.py
from flask import Flask, jsonify, request
from flask_cors import CORS

from ping.arp import arp_ping
from ping.icmp import icmp_ping
from ping.tcp import tcp_ping
from ping.udp import udp_ping

app = Flask(__name__)
CORS(app)


@app.route("/api/test", methods=["GET"])
def run_test():
    return jsonify({"message": "Test endpoint is working!"})


@app.route("/api/ping/icmp", methods=["GET"])
def run_icmp_ping():
    host = request.args.get("host", type=str)
    if not host:
        return jsonify({"error": "Host parameter is required"}), 400
    try:
        result = icmp_ping(host)  # ensure this returns a JSON-safe dict
        return jsonify(result)
    except PermissionError:
        return jsonify({"error": "ICMP requires admin/root privileges on this OS"}), 500


@app.route("/api/ping/tcp", methods=["GET"])
def run_tcp_ping():
    host = request.args.get("host", type=str)
    port = request.args.get("port", type=int)
    if not host or port is None:
        return jsonify({"error": "Host and port parameters are required"}), 400
    result = tcp_ping(host, port)  # ensure JSON-safe return
    return jsonify(result)


@app.route("/api/ping/arp", methods=["GET"])
def run_arp_ping():
    host = request.args.get("host", type=str)
    if not host:
        return jsonify({"error": "Host parameter is required"}), 400
    result = arp_ping(host)  # ensure JSON-safe return
    return jsonify(result)


@app.route("/api/ping/udp", methods=["GET"])
def run_udp_ping():
    host = request.args.get("host", type=str)
    if not host:
        return jsonify({"error": "Host parameter is required"}), 400
    result = udp_ping(host)  # ensure JSON-safe return
    return jsonify(result)
    return jsonify(result)
    result = tcp_ping(host, port)  # ensure JSON-safe return
    return jsonify(result)


if __name__ == "__main__":
    # For dev: avoid double-run issues with raw sockets
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)
