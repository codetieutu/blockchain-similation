import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
import uuid
import time

load_dotenv()


class WalletApp(tk.Tk):
    """Chạy độc lập: Wallet là một ứng dụng Tk riêng."""

    def __init__(self):
        super().__init__()
        self.title("Simple Wallet")
        self.geometry("520x520")
        self.configure(bg="white")

        self.api_base = os.getenv("INDEX_ADDRESS")
        # ---- state / properties ----
        self._address = ""
        self._balance = 0.0

        # tk vars
        self.wallet_var = tk.StringVar(value="")
        self.balance_var = tk.StringVar(value="0")
        self.to_var = tk.StringVar(value="")
        self.amount_var = tk.StringVar(value="")

        self._build_ui()
        self.poll_interval_ms = 1000
        self._poll_job = None
        self._last_balance = None

        self._start_polling()
        self.protocol("WM_DELETE_WINDOW", self.on_close)


    # =====================
    # Properties
    # =====================
    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value: str):
        value = (value or "").strip()
        self._address = value
        self.wallet_var.set(value)
        self.refresh_balance(force=True)

    @property
    def balance(self) -> float:
        return float(self._balance)

    @balance.setter
    def balance(self, value: float):
        try:
            self._balance = float(value)
        except Exception:
            self._balance = 0.0
        self.balance_var.set(f"{self._balance:g}")

    # =====================
    # UI
    # =====================
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg="#2c3e50", padx=14, pady=12)
        header.pack(fill="x")

        tk.Label(header, text="Wallet", font=("Arial", 14, "bold"),
                 fg="white", bg="#2c3e50").pack(side="left")

        tk.Button(
            header, text="⟳ Refresh",
            command=lambda: self.refresh_balance(force=True),
            font=("Arial", 10, "bold"),
            fg="white", bg="#34495e",
            activebackground="#3d566e",
            relief="flat", padx=10, pady=6
        ).pack(side="right")

        # Address
        card_addr = tk.LabelFrame(self, text="Wallet Address", bg="white", font=("Arial", 10, "bold"))
        card_addr.pack(fill="x", padx=12, pady=(12, 8))

        row = tk.Frame(card_addr, bg="white")
        row.pack(fill="x", padx=10, pady=10)

        tk.Entry(row, textvariable=self.wallet_var, font=("Consolas", 11)).pack(
            side="left", fill="x", expand=True
        )

        tk.Button(
            row, text="Set",
            command=self._set_wallet_address,
            font=("Arial", 10, "bold"),
            bg="#3498db", fg="white",
            activebackground="#2980b9",
            relief="flat", padx=12, pady=6
        ).pack(side="left", padx=(8, 0))

        # Balance
        card_bal = tk.LabelFrame(self, text="Balance", bg="white", font=("Arial", 10, "bold"))
        card_bal.pack(fill="x", padx=12, pady=(0, 10))

        bal_row = tk.Frame(card_bal, bg="white")
        bal_row.pack(fill="x", padx=10, pady=10)

        self.lbl_balance = tk.Label(
            bal_row, textvariable=self.balance_var,
            font=("Consolas", 20, "bold"),
            bg="white", fg="#2ecc71"
        )
        self.lbl_balance.pack(anchor="w")

        # Transfer
        card_tx = tk.LabelFrame(self, text="Transfer", bg="white", font=("Arial", 10, "bold"))
        card_tx.pack(fill="x", padx=12, pady=(0, 10))

        to_row = tk.Frame(card_tx, bg="white")
        to_row.pack(fill="x", padx=10, pady=(10, 6))
        tk.Label(to_row, text="To:", bg="white", font=("Arial", 10)).pack(side="left")
        tk.Entry(to_row, textvariable=self.to_var, font=("Consolas", 11)).pack(
            side="left", fill="x", expand=True, padx=(8, 0)
        )

        amt_row = tk.Frame(card_tx, bg="white")
        amt_row.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(amt_row, text="Amount:", bg="white", font=("Arial", 10)).pack(side="left")
        tk.Entry(amt_row, textvariable=self.amount_var, font=("Consolas", 11)).pack(
            side="left", fill="x", expand=True, padx=(8, 0)
        )

        tk.Button(
            card_tx, text="Send",
            command=self.send_transaction,
            font=("Arial", 11, "bold"),
            bg="#27ae60", fg="white",
            activebackground="#1e8449",
            relief="flat", padx=12, pady=8
        ).pack(anchor="e", padx=10, pady=(0, 10))

        # Logs
        card_log = tk.LabelFrame(self, text="Logs", bg="white", font=("Arial", 10, "bold"))
        card_log.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.log_text = tk.Text(card_log, wrap="word", font=("Consolas", 10), bg="#fbfbfb")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text.configure(state="disabled")

    # =====================
    # Actions
    # =====================
    def _set_wallet_address(self):
        addr = self.wallet_var.get().strip()
        if not addr:
            messagebox.showwarning("Missing", "Please enter a wallet address.")
            return
        self.address = addr
        self.add_log(f"Wallet set: {addr}")
        self.refresh_balance(force=True)


    def _start_polling(self):
        self._stop_polling()
        self._poll_job = self.after(self.poll_interval_ms, self._poll_tick)

    def _stop_polling(self):
        if self._poll_job is not None:
            try:
                self.after_cancel(self._poll_job)
            except Exception:
                pass
            self._poll_job = None

    def _poll_tick(self):
        # chỉ poll khi đã set address
        if self.address:
            self.refresh_balance(force=False, log_on_change=True)
        self._poll_job = self.after(self.poll_interval_ms, self._poll_tick)

    def on_close(self):
        self._stop_polling()
        self.destroy()
        

    def refresh_balance(self, force=False, log_on_change=False):
        if not self.address:
            self.balance = 0
            self.lbl_balance.configure(fg="#e74c3c")
            return

        try:
            r = requests.get(f"{self.api_base}/balance/{self.address}", timeout=5)
            r.raise_for_status()
            data = r.json()
            bal = float(data.get("balance", 0))

            changed = (self._last_balance is None) or (bal != self._last_balance)
            self._last_balance = bal

            self.balance = bal
            self.lbl_balance.configure(fg="#2ecc71" if bal >= 0 else "#e74c3c")

            if force:
                self.add_log(f"Balance updated: {bal:g}")
            elif log_on_change and changed:
                self.add_log(f"[POLL] Balance changed: {bal:g}")

        except Exception as e:
            # polling tránh spam log mỗi giây
            if force:
                self.add_log(f"[BAL] Error: {e}")
            self.lbl_balance.configure(fg="#e74c3c")
            # KHÔNG set balance=0 ở đây để khỏi nhảy số khi backend lag



    def send_transaction(self):
        from_addr = self.address
        to_addr = self.to_var.get().strip()
        amt_raw = self.amount_var.get().strip()

        if not from_addr:
            messagebox.showwarning("Missing", "Please set your wallet address first.")
            return
        if not to_addr:
            messagebox.showwarning("Missing", "Please enter recipient address.")
            return
        if not amt_raw:
            messagebox.showwarning("Missing", "Please enter amount.")
            return

        # parse amount
        try:
            amount = float(amt_raw)
            if amount <= 0:
                raise ValueError("Amount must be > 0")
        except Exception:
            messagebox.showerror("Invalid", "Amount must be a valid number > 0.")
            return

        # check balance (đúng logic)
        try:
            if amount > float(self.balance):
                messagebox.showerror("Insufficient", f"Insufficient balance. Current: {self.balance:g}")
                return
        except Exception:
            messagebox.showerror("Error", "Cannot check balance right now.")
            return

        transaction = {
            "from": from_addr,
            "to": to_addr,
            "amount": amount,
            "timestamp": time.time()
        }

        payload = {
            "tx_id": str(uuid.uuid4()),
            "transaction": transaction
        }

        try:
            r = requests.post(f"{self.api_base}/transactions/new", json=payload, timeout=5)

            if r.status_code not in (200, 201):
                try:
                    msg = r.json().get("message", r.text)
                except Exception:
                    msg = r.text
                raise Exception(f"HTTP {r.status_code}: {msg}")

            try:
                msg = r.json().get("message", "OK")
            except Exception:
                msg = "OK"

            self.add_log(f"[TX] Submitted tx_id={payload['tx_id']} | {transaction} | {msg}")
            messagebox.showinfo("Success", msg)

        except Exception as e:
            self.add_log(f"[TX] Error: {e}")
            messagebox.showerror("Error", str(e))
            return

        self.to_var.set("")
        self.amount_var.set("")
        self.refresh_balance(force=True)


    def add_log(self, msg: str):
        t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{t}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


if __name__ == "__main__":
    app = WalletApp() 
    app.mainloop()
