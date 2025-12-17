# api.py
from flask import Response, request, jsonify
from block import Block
import requests
import threading
import queue
import json

seen_tx = set()

def register_routes(app, blockchain, peers, memPool, add_log, stop_mining_event):
    """
    Hàm này nhận vào:
      - app: Flask app
      - blockchain: đối tượng Blockchain
      - peers: tập (set) các peer URL
    Và đăng ký toàn bộ route cho app.
    """

    # ---------- ROUTES ----------

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "message": "Node blockchain đang chạy",
            "peers": list(peers),
            "chain_length": len(blockchain.chain),
        })

    @app.route("/peers", methods=["GET"])
    def getpeers():
        return jsonify({
            "peers": list(peers)
        })

    @app.route("/chain", methods=["GET"])
    def get_chain():
        return jsonify({
            "length": len(blockchain.chain),
            "chain": blockchain.to_dict()
        })

    @app.route("/transactions/new", methods=["POST"])
    def new_transaction():
     
        data = request.get_json()

        tx_id = data.get("tx_id")
        if not tx_id:
            return jsonify({"message": "Missing tx_id"}), 400
        
        if tx_id in seen_tx:
            return jsonify({"message": "Tx already seen"}), 200

        add_log("nhận được thông tin 1 giao dịch")
        seen_tx.add(tx_id)
        memPool.append(data.get("transaction"))

        for peer in list(peers):
            url = f"{peer}/transactions/new"
            try:
                requests.post(url, json={data}, timeout=3)
            except Exception as e:
                print(f"⚠ Không gửi được block tới {peer}: {e}")


        return jsonify({"message": "Đã thêm transaction vào pending"}), 201

    @app.route("/blocks/receive", methods=["POST"])
    def receive_block():
        """
        Nhận block từ node khác.
        Body JSON: block dict
        """
        block_data = request.get_json()
        add_log("nhận được block từ node khác")
        try:
            block = Block.from_dict(block_data)
        except Exception as e:
            add_log("block không hợp lệ")
            return jsonify({"error": f"Block data không hợp lệ: {e}"}), 400

        ok = blockchain.add_block_from_peer(block)
        if not ok:
            sync_chain = threading.Thread(target=blockchain.sync_chain, args=(peers, add_log,))
            sync_chain.start()
            add_log("block không hợp lệ")
            return jsonify({"message": "Block bị từ chối"}), 400
        
        stop_mining_event.set()
        add_log("block hợp lệ, đã thêm vào blockchain")
    
        return jsonify({"message": "Đã nhận và thêm block từ peer"}), 201

    @app.route("/peers/add", methods=["POST"])
    def add_peer():
        """
        Body JSON: {"peer": "http://localhost:5002"}
        """
        data = request.get_json()
        peer = data.get("peer")
        if not peer:
            return jsonify({"error": "Thiếu peer"}), 400

        peers.add(peer)
        add_log("có 1 node tham gia vào mạng lưới")
        return jsonify({"message": "Đã thêm peer", "peers": list(peers)}), 201

    @app.route("/balance/<address>", methods=["GET"])
    def get_balance(address):
        try:
            bal = blockchain.get_balance(address)
            return jsonify({
                "address": address,
                "balance": bal
            }), 200
        except Exception as e:
            return jsonify({
                "error": str(e)
            }), 500

def broadcast_new_block(block, peers):
    """
    Hàm gửi block mới đã mine tới tất cả peers.
    (Không phải route, chỉ là helper được dùng trong /mine)
    """
    block_data = block.to_dict()
    for peer in list(peers):
        url = f"{peer}/blocks/receive"
        try:
            res = requests.post(url, json=block_data, timeout=3)
            print(f"→ Gửi block tới {peer}, status {res.status_code}")
        except Exception as e:
            print(f"⚠ Không gửi được block tới {peer}: {e}")
