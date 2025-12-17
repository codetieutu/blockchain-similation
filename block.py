# block.py
import hashlib
import json
import time


class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0, block_hash=None):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions      
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = block_hash or self.calculate_hash()

    def calculate_hash(self):
        payload = {
            "index": int(self.index),
            "timestamp": self.timestamp,          # hoặc ép int, xem ghi chú dưới
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": int(self.nonce),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def mine(self, difficulty, stop_mining_event):
        target_prefix = "0" * difficulty
        while not stop_mining_event.is_set():
            self.hash = self.calculate_hash()
            if self.hash.startswith(target_prefix):
                break
            self.nonce += 1

    @staticmethod
    def create_genesis_block():
        return Block(
            index=0,
            timestamp=1672531200,
            transactions=[{"from": "System", "to": "Genesis", "amount": 0}],
            previous_hash="0" * 64
        )

    def to_dict(self):
        """Dùng để serialize block gửi cho node khác (JSON)"""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @staticmethod
    def from_dict(data: dict):
        """Dùng để dựng lại Block khi nhận JSON từ node khác"""
        return Block(
            index=data["index"],
            timestamp=data["timestamp"],
            transactions=data["transactions"],
            previous_hash=data["previous_hash"],
            nonce=data["nonce"],
            block_hash=data["hash"],
        )
