# gui.py
import tkinter as tk
from tkinter import ttk
from datetime import datetime

class NodeGUI:
    def __init__(self, root, blockchain, peers):
        self.root = root
        self.blockchain = blockchain
        self.peers = peers

        self.root.title("Simple Blockchain Node")
        self.root.geometry("1000x500")

        # ====== KHUNG CHÍNH ======
        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Dùng grid cho top (Blocks + Peers)
        top_frame = tk.Frame(main_frame)
        top_frame.pack(side="top", fill="both", expand=True)

        # ====== CẤU HÌNH GRID ======
        top_frame.columnconfigure(0, weight=8)   # 70%
        top_frame.columnconfigure(1, weight=2)   # 30%
        top_frame.rowconfigure(0, weight=1)

        # ====== KHUNG BLOCKS (cột 0 - chiếm 70%) ======
        left_frame = tk.Frame(top_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Label(left_frame, text="Blocks", font=("Arial", 12, "bold")).pack(anchor="w")
        self.block_list = tk.Listbox(left_frame, font=("Consolas", 10))
        self.block_list.pack(fill="both", expand=True, pady=(5, 0))
        self.block_list.bind("<<ListboxSelect>>", self.show_block_details)


        # ====== KHUNG PEERS (cột 1 - chiếm 30%) ======
        right_frame = tk.Frame(top_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")

        tk.Label(right_frame, text="Peers", font=("Arial", 12, "bold")).pack(anchor="w")
        self.peer_list = tk.Listbox(right_frame, font=("Consolas", 10))
        self.peer_list.pack(fill="both", expand=True, pady=(5, 0))

        # ====== KHUNG LOG (BÊN DƯỚI) ======
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(side="bottom", fill="x", pady=(10, 0))

        tk.Label(bottom_frame, text="Logs", font=("Arial", 12, "bold")).pack(anchor="w")

        log_container = tk.Frame(bottom_frame)
        log_container.pack(fill="x")

        self.log_text = tk.Text(log_container, font=("Consolas", 10), height=6)
        self.log_text.pack(side="left", fill="x", expand=True)

        log_scroll = tk.Scrollbar(log_container, command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scroll.set)

        # ====== NÚT REFRESH ======
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", pady=5)

        refresh_btn = tk.Button(btn_frame, text="Refresh", command=self.refresh)
        refresh_btn.pack()

        self._refresh_scheduled = False

        if hasattr(self.blockchain, "subscribe"):
            self.blockchain.subscribe(self.on_data_changed)
        if hasattr(self.peers, "subscribe"):
            self.peers.subscribe(self.on_data_changed)

        self.refresh()

    def add_log(self, msg):
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{time}] : {msg} \n")
        self.log_text.see(tk.END)

    def refresh(self):
        # Cập nhật danh sách block
        self.block_list.delete(0, tk.END)
        for i, block in enumerate(self.blockchain.chain):
            index = getattr(block, "index", i)
            bhash = getattr(block, "hash", getattr(block, "current_hash", "")) 
            prev = getattr(block, "previous_hash", "")
            line = f"#{index} | hash: {str(bhash)[:16]}... | prev: {str(prev)[:16]}..."
            self.block_list.insert(tk.END, line)

        # Cập nhật danh sách peers
        self.peer_list.delete(0, tk.END)
        for peer in sorted(self.peers):
            self.peer_list.insert(tk.END, peer)
    
    def on_data_changed(self):
        if self._refresh_scheduled:
            return
        self._refresh_scheduled = True
        # đảm bảo refresh chạy trên main thread của Tkinter
        self.root.after(0, self._do_refresh)

    def _do_refresh(self):
        self._refresh_scheduled = False
        self.refresh()

    def show_block_details(self, event):
        selection = self.block_list.curselection()
        if not selection:
            return

        index = selection[0]

        # Lấy block từ blockchain (list hoặc method của bạn)
        try:
            block = self.blockchain.chain[index]
        except Exception:
            self.add_log("Không lấy được block chi tiết")
            return

        # Mở cửa sổ popup
        detail_win = tk.Toplevel(self.root)
        detail_win.title(f"Block #{block.index} Details")
        detail_win.geometry("600x500")

        # Khung text hiển thị chi tiết block
        text = tk.Text(detail_win, font=("Consolas", 11), wrap="none")
        text.pack(fill="both", expand=True)

        # Scrollbar ngang + dọc
        scroll_y = tk.Scrollbar(detail_win, orient="vertical", command=text.yview)
        scroll_y.pack(side="right", fill="y")
        text.configure(yscrollcommand=scroll_y.set)

        scroll_x = tk.Scrollbar(detail_win, orient="horizontal", command=text.xview)
        scroll_x.pack(side="bottom", fill="x")
        text.configure(xscrollcommand=scroll_x.set)

        # Format block dưới dạng JSON đẹp
        import json
        block_dict = block.to_dict() if hasattr(block, "to_dict") else block.__dict__

        pretty = json.dumps(block_dict, indent=4, ensure_ascii=False)

        # Hiển thị vào text
        text.insert("1.0", pretty)
        text.configure(state="disabled")

