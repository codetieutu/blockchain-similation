# node_dashboard_gui.py
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime


class BlockDetailWindow(tk.Toplevel):
    def __init__(self, master, block):
        super().__init__(master)
        self.title(f"Block #{block.index} details")
        self.geometry("650x500")
        self.configure(bg="white")

        header = tk.Frame(self, bg="white")
        header.pack(fill="x", padx=12, pady=10)

        tk.Label(
            header,
            text=f"Block #{block.index}",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(side="left")

        body = tk.Frame(self, bg="white")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        txt = tk.Text(body, wrap="word", font=("Consolas", 10), bg="#fbfbfb")
        txt.pack(fill="both", expand=True)

        # Pretty print block
        detail = {
            "index": block.index,
            "timestamp": block.timestamp,
            "timestamp_readable": self._fmt_time(block.timestamp),
            "previous_hash": block.previous_hash,
            "nonce": block.nonce,
            "hash": block.hash,
            "transactions": block.transactions,
        }

        txt.insert("1.0", json.dumps(detail, ensure_ascii=False, indent=2))
        txt.configure(state="disabled")

    @staticmethod
    def _fmt_time(ts):
        try:
            return datetime.fromtimestamp(float(ts)).isoformat(sep=" ", timespec="seconds")
        except Exception:
            return str(ts)


class NodeGUI(tk.Frame):
    """
    GUI dashboard:
    - Header: node address, wallet address, balance
    - Left: list blocks (Treeview)
    - Right-top: peers list
    - Bottom: log area
    Auto refresh by polling + snapshot.
    """

    def __init__(self, master, blockchain, peers, node_address, wallet_address):
        super().__init__(master, bg="white")
        self.master = master
        self.blockchain = blockchain
        self.peers = peers
        self.node_address = node_address
        self.wallet_address = wallet_address  

        # --- snapshots to detect changes ---
        self._last_tip_hash = None
        self._last_chain_len = -1
        self._last_peers_snapshot = None
        self._last_balance = None

        self._build_ui()
        self.pack(fill="both", expand=True)
        if hasattr(self.blockchain, "subscribe"):
            self.blockchain.subscribe(self.refresh_all)
        if hasattr(self.peers, "subscribe"):
            self.peers.subscribe(self.refresh_all)
        self.add_log("đã khởi động")
        # initial paint
        self.refresh_all(force=True)


    # ---------------- UI ----------------
    def _build_ui(self):
        self.master.title("Blockchain Node Dashboard")
        self.master.geometry("980x640")
        self.master.configure(bg="white")

        # ===== Header =====
        header = tk.Frame(self, bg="#2c3e50")
        header.pack(fill="x")

        header.grid_columnconfigure(0, weight=3)
        header.grid_columnconfigure(1, weight=3)
        header.grid_columnconfigure(2, weight=1)

        # Node address
        node_frame = tk.Frame(header, bg="#2c3e50", padx=14, pady=12)
        node_frame.grid(row=0, column=0, sticky="w")

        tk.Label(node_frame, text="Node Address", font=("Arial", 9, "bold"),
                 fg="#bdc3c7", bg="#2c3e50").pack(anchor="w")
        self.lbl_node = tk.Label(node_frame, text=self.node_address,
                                 font=("Consolas", 12, "bold"),
                                 fg="#3498db", bg="#2c3e50")
        self.lbl_node.pack(anchor="w")

        # Wallet address + balance
        wallet_frame = tk.Frame(header, bg="#2c3e50", padx=14, pady=12)
        wallet_frame.grid(row=0, column=1, sticky="w")

        tk.Label(wallet_frame, text="Wallet Address", font=("Arial", 9, "bold"),
                 fg="#bdc3c7", bg="#2c3e50").pack(anchor="w")
        self.lbl_wallet = tk.Label(wallet_frame, text=self.wallet_address,
                                   font=("Consolas", 12, "bold"),
                                   fg="#f1c40f", bg="#2c3e50")
        self.lbl_wallet.pack(anchor="w")

        bal_line = tk.Frame(wallet_frame, bg="#2c3e50")
        bal_line.pack(anchor="w", pady=(6, 0))
        tk.Label(bal_line, text="Balance:", font=("Arial", 10, "bold"),
                 fg="#bdc3c7", bg="#2c3e50").pack(side="left")
        self.balance_var = tk.StringVar(value="0")
        self.lbl_balance = tk.Label(bal_line, textvariable=self.balance_var,
                                    font=("Consolas", 14, "bold"),
                                    fg="#2ecc71", bg="#2c3e50")
        self.lbl_balance.pack(side="left", padx=(8, 0))

        # Refresh button
        control_frame = tk.Frame(header, bg="#2c3e50", padx=14, pady=12)
        control_frame.grid(row=0, column=2, sticky="e")

        self.btn_refresh = tk.Button(
            control_frame,
            text="⟳ Refresh",
            command=lambda: self.refresh_all(force=True),
            font=("Arial", 10, "bold"),
            fg="white",
            bg="#34495e",
            activebackground="#3d566e",
            relief="flat",
            padx=14,
            pady=8,
        )
        self.btn_refresh.pack(anchor="e")

        # ===== Main content =====
        main = tk.Frame(self, bg="white")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        main.grid_rowconfigure(0, weight=7)  # top area
        main.grid_rowconfigure(1, weight=3)  # log area
        main.grid_columnconfigure(0, weight=7)  # blocks
        main.grid_columnconfigure(1, weight=3)  # peers

        # ---- Blocks panel ----
        blocks_card = tk.LabelFrame(main, text="Blocks", bg="white", font=("Arial", 10, "bold"))
        blocks_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        blocks_card.grid_rowconfigure(0, weight=1)
        blocks_card.grid_columnconfigure(0, weight=1)

        self.blocks_tree = ttk.Treeview(
            blocks_card,
            columns=("index", "txs", "time", "hash"),
            show="headings",
            height=14
        )
        self.blocks_tree.heading("index", text="#")
        self.blocks_tree.heading("txs", text="Txs")
        self.blocks_tree.heading("time", text="Time")
        self.blocks_tree.heading("hash", text="Hash")

        self.blocks_tree.column("index", width=60, anchor="center")
        self.blocks_tree.column("txs", width=60, anchor="center")
        self.blocks_tree.column("time", width=170, anchor="w")
        self.blocks_tree.column("hash", width=360, anchor="w")

        sb_blocks = ttk.Scrollbar(blocks_card, orient="vertical", command=self.blocks_tree.yview)
        self.blocks_tree.configure(yscrollcommand=sb_blocks.set)

        self.blocks_tree.grid(row=0, column=0, sticky="nsew")
        sb_blocks.grid(row=0, column=1, sticky="ns")

        self.blocks_tree.bind("<<TreeviewSelect>>", self._on_block_selected)
        self._block_by_iid = {}

        # ---- Peers panel ----
        peers_card = tk.LabelFrame(main, text="Peers", bg="white", font=("Arial", 10, "bold"))
        peers_card.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        peers_card.grid_rowconfigure(0, weight=1)
        peers_card.grid_columnconfigure(0, weight=1)

        self.peers_list = tk.Listbox(peers_card, font=("Consolas", 10))
        sb_peers = ttk.Scrollbar(peers_card, orient="vertical", command=self.peers_list.yview)
        self.peers_list.configure(yscrollcommand=sb_peers.set)

        self.peers_list.grid(row=0, column=0, sticky="nsew")
        sb_peers.grid(row=0, column=1, sticky="ns")

        # ---- Log panel ----
        log_card = tk.LabelFrame(main, text="Log", bg="white", font=("Arial", 10, "bold"))
        log_card.grid(row=1, column=0, columnspan=2, sticky="nsew")
        log_card.grid_rowconfigure(0, weight=1)
        log_card.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_card, wrap="word", font=("Consolas", 10), bg="#fbfbfb", height=8)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        sb_log = ttk.Scrollbar(log_card, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb_log.set)
        sb_log.grid(row=0, column=1, sticky="ns")

        self.log_text.configure(state="disabled")

    def refresh_all(self, force=False):
        self._refresh_blocks(force=force)
        self._refresh_peers(force=force)

    # def _refresh_balance(self, force=False):
    #     try:
    #         bal = self.blockchain.get_balance(self.wallet_address)
    #     except Exception as e:
    #         self.add_log(f"[BAL] Error: {e}")
    #         bal = 0

    #     if force or bal != self._last_balance:
    #         self._last_balance = bal
    #         self.balance_var.set(f"{bal:g}")
    #         # color
    #         self.lbl_balance.configure(fg="#2ecc71" if float(bal) >= 0 else "#e74c3c")

    def _refresh_blocks(self, force=False):
        chain = getattr(self.blockchain, "chain", [])
        chain_len = len(chain)

        tip_hash = None
        if chain_len > 0:
            tip = chain[-1]
            tip_hash = getattr(tip, "hash", None)

        changed = force or (chain_len != self._last_chain_len) or (tip_hash != self._last_tip_hash)

        if not changed:
            return

        self._last_chain_len = chain_len
        self._last_tip_hash = tip_hash

        # rebuild list
        self.blocks_tree.delete(*self.blocks_tree.get_children())
        self._block_by_iid.clear()

        for b in chain:
            iid = f"b{b.index}"
            tx_count = len(b.transactions) #if isinstance(b.transactions, list) else 0
            time_str = self._fmt_time(getattr(b, "timestamp", ""))
            h = getattr(b, "hash", "")
            short_hash = (h[:22] + "…") if isinstance(h, str) and len(h) > 23 else h

            self.blocks_tree.insert(
                "", "end",
                iid=iid,
                values=(b.index, tx_count, time_str, short_hash)
            )
            self._block_by_iid[iid] = b


    def _refresh_peers(self, force=False):
        # snapshot peers as tuple of strings
        try:
            peers_snapshot = tuple(map(str, list(self.peers)))
        except Exception:
            peers_snapshot = tuple()

        if not (force or peers_snapshot != self._last_peers_snapshot):
            return

        self._last_peers_snapshot = peers_snapshot

        self.peers_list.delete(0, tk.END)
        for p in peers_snapshot:
            self.peers_list.insert(tk.END, p)


    # -------------- Block click --------------
    def _on_block_selected(self, _evt):
        sel = self.blocks_tree.selection()
        if not sel:
            return
        iid = sel[0]
        block = self._block_by_iid.get(iid)
        if not block:
            return
        BlockDetailWindow(self.master, block)

    # -------------- Log --------------
    def add_log(self, msg: str):
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # bật lên để ghi
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, f"[{time}] : {msg}\n")
        self.log_text.see(tk.END)
        # khoá lại để user không sửa
        self.log_text.configure(state="disabled")

    @staticmethod
    def _fmt_time(ts):
        try:
            return datetime.fromtimestamp(float(ts)).isoformat(sep=" ", timespec="seconds")
        except Exception:
            return str(ts)