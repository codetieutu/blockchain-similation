# node.py
from flask import Flask
from ObservablePeers import ObservablePeers
from blockchain import Blockchain
from api import register_routes
from MainView import NodeGUI
import requests
from dotenv import load_dotenv
import time

import threading
import os
import tkinter as tk
import random
import string

# ====== TẠO NODE (blockchain + flask) ======
blockchain = Blockchain(difficulty=5)
peers = ObservablePeers()
memPool = []

load_dotenv()
INDEX_ADDRESS = os.getenv("INDEX_ADDRESS")
MY_ADDRESS = os.getenv("MY_ADDRESS")

app = Flask(__name__)

def generate_address(length=12):
    chars = string.ascii_uppercase + string.digits
    return "NODE_" + "".join(random.choice(chars) for _ in range(length))

def get_port():
    return int(os.environ.get("PORT", 5001))

def miner(stop_event):
    global memPool

    while True:
        try:
            if len(memPool) > 0:
                gui.add_log("đang đào block mới")
                stop_event.clear()
                new_block = blockchain.miner(memPool, stop_event, add_log=gui.add_log)

                if(new_block):
                    try:
                        gui.add_log("đang broadcast đến các node khác")
                        for peer in peers:
                            res = requests.post(f"{peer}/blocks/receive", json=new_block.to_dict())
                        gui.add_log("broadcast xong")
                    except Exception as e:
                        print("lỗi1: ", e)
        except Exception as e:
            print("lỗi2: ", e)
        time.sleep(1)

def run_flask():
    """
    Chạy Flask server trong thread riêng.
    use_reloader=False để tránh tạo process phụ.
    """
    port = get_port()
    print(f"Đang chạy node Flask trên port {port}...")
    app.run(host="0.0.0.0", port=port, use_reloader=False)


if __name__ == "__main__":

    root = tk.Tk()
    gui = NodeGUI(root, blockchain, peers, MY_ADDRESS ,wallet_address=generate_address())
    stop_mining_event = threading.Event()
    register_routes(app, blockchain, peers, memPool, gui.add_log, stop_mining_event)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print("my address", MY_ADDRESS)
    print("index address", INDEX_ADDRESS)

    if MY_ADDRESS != INDEX_ADDRESS:
        try:
            gui.add_log("đang lấy thông tin các node khác từ index")
            peers.add(INDEX_ADDRESS)

            res = requests.get(f"{INDEX_ADDRESS}/peers", timeout=3)
            data = res.json()
            peers.update(data.get("peers", []))
            blockchain.sync_chain(peers, gui.add_log)
            gui.add_log("đã cập nhậ dữ liệu")
            for peer in peers:
                requests.post(f"{peer}/peers/add", json={"peer":f"{MY_ADDRESS}"})
            blockchain.sync_chain(peers, gui.add_log)
        except requests.RequestException as e:
            print("Không kết nối được đến bootstrap node:", e)

    # 3) Chạy Tkinter GUI trong thread chính (nếu bạn dùng GUI)
    
    miner_thread = threading.Thread(target=miner, args = (stop_mining_event,),daemon=True)
    miner_thread.start()

    root.mainloop()
