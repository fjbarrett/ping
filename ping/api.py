# api.py
from flask import Flask, jsonify, request
from flask_cors import CORS

from ping.arp import arp_ping
from ping.icmp import icmp_ping
from ping.tcp import tcp_ping
from ping.udp import udp_ping
from ping.rdns import rdns_lookup

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def run_health_check():
    return jsonify({"message": "Health check is working!"})


@app.route("/api/ping/rdns", methods=["GET"])
def run_rdns_lookup():
    ip = request.args.get("ip", type=str)
    if not ip:
        return jsonify({"error": "IP parameter is required"}), 400
    result = rdns_lookup(ip)  # ensure this returns a JSON-safe dict
    return jsonify(result)


@app.route("/api/ping/icmp", methods=["GET"])
def run_icmp_ping():
    host = request.args.get("host", type=str)
    if not host:
        return jsonify({"error": "Host parameter is required"}), 400
    count = request.args.get("count", type=int, default=4)
    timeout = request.args.get("timeout", type=float, default=1.0)
    try:
        result = icmp_ping(host, count=count, timeout=timeout)
        return jsonify(result)
    except PermissionError:
        return jsonify({"error": "ICMP requires admin/root privileges on this OS"}), 500


@app.route("/api/ping/tcp", methods=["GET"])
def run_tcp_ping():
    host = request.args.get("host", type=str)
    port = request.args.get("port", type=int)
    timeout = request.args.get("timeout", type=float, default=5.0)
    if not host or port is None:
        return jsonify({"error": "Host and port parameters are required"}), 400
    if not (1 <= port <= 65535):
        return jsonify({"error": "Port must be between 1 and 65535"}), 400
    result = tcp_ping(host, port, timeout=timeout)
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
    port = request.args.get("port", type=int, default=53000)
    timeout = request.args.get("timeout", type=float, default=1.0)
    if not host:
        return jsonify({"error": "Host parameter is required"}), 400
    if not (1 <= port <= 65535):
        return jsonify({"error": "Port must be between 1 and 65535"}), 400
    result = udp_ping(host, port=port, timeout=timeout)
    return jsonify(result)


if __name__ == "__main__":
    # For dev: avoid double-run issues with raw sockets
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)
