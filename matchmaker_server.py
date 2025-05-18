from flask import Flask, request, jsonify
import threading

app = Flask(__name__)
pending = {}

@app.route("/connect", methods=["POST"])
def connect():
    data = request.json
    me = data["self"]
    peer = data["peer"]
    port = data["port"]
    ip = request.remote_addr

    # Есть ли ожидающий собеседник?
    if peer in pending and pending[peer]["peer"] == me:
        peer_info = pending.pop(peer)
        return jsonify({
            "role": "sender",
            "ip": peer_info["ip"],
            "port": peer_info["port"]
        })

    # Иначе ждем...
    pending[me] = {"peer": peer, "ip": ip, "port": port}
    return jsonify({"role": "receiver"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
