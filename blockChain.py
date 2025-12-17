# blockchain.py
from block import Block
import time
import requests


class Blockchain:
    def __init__(self, difficulty=3):
        self.difficulty = difficulty
        self.chain = [Block.create_genesis_block()]
        self._subscribers = []

    def subscribe(self, callback):
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify(self):
        for cb in list(self._subscribers):
            try:
                cb()
            except Exception as e:
                print("Notify error:", e)

    def get_latest_block(self):
        return self.chain[-1]

    # ---------- MINING (LOCAL NODE) ----------
    def miner(self, tx_data, stop_event, add_log):
        """
        Tạo block mới từ pending_transactions, thưởng cho miner,
        rồi clear pending.
        """
        
        previous_block = self.get_latest_block()
        new_block = Block(
            index=previous_block.index + 1,
            timestamp=time.time(),
            transactions=list(tx_data),
            previous_hash=previous_block.hash,
            nonce=0
        )
        tx_data.clear()
        new_block.mine(self.difficulty, stop_mining_event = stop_event)
        if stop_event.is_set():
            add_log("đã dừng đào")
            return None
        
        if self.is_valid_new_block(new_block, previous_block):
            add_log("đã đào xong ")
            self.chain.append(new_block)
            self._notify();

            return new_block
        else:
            print("❌ Block mới không hợp lệ, không thêm vào chain!")
            return None

    # ---------- NHẬN BLOCK TỪ NODE KHÁC ----------
    def add_block_from_peer(self, block: Block):
        """
        Khi node khác gửi block đã mine xong.
        """
        previous_block = self.get_latest_block()

        # Block phải là block kế tiếp
        if block.index != previous_block.index + 1:
            print("❌ Block từ peer có index không khớp, bỏ qua.")
            return False

        if not self.is_valid_new_block(block, previous_block):
            print("❌ Block từ peer không hợp lệ, bỏ qua.")
            return False

        self.chain.append(block)
        self._notify()
        print(f"✅ Đã thêm block {block.index} từ peer vào chain.")
        return True

    # ---------- VALIDATION ----------
    def is_valid_new_block(self, new_block: Block, previous_block: Block):
        # 1. index
        if new_block.index != previous_block.index + 1:
            print("❌ Sai index")
            return False

        # 2. previous_hash
        if new_block.previous_hash != previous_block.hash:
            print("❌ previous_hash không khớp")
            return False

        # 3. hash có đúng với dữ liệu + nonce không
        recalculated_hash = new_block.calculate_hash()

        if new_block.hash != recalculated_hash:
            print("❌ Hash không khớp calculate_hash()")
            return False

        # 4. PoW: hash phải bắt đầu bằng N số 0
        target_prefix = "0" * self.difficulty
        if not new_block.hash.startswith(target_prefix):
            print("❌ PoW không hợp lệ (hash không đủ số 0 ở đầu)")
            return False

        return True

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if not self.is_valid_new_block(current, previous):
                print(f"❌ Blockchain không hợp lệ tại block {i}")
                return False

        print("✅ Blockchain hợp lệ")
        return True

    # phụ: convert chain sang list dict để trả JSON
    def to_dict(self):
        return [block.to_dict() for block in self.chain]
    
    def _validate_external_chain(self, chain_list):
        """
        chain_list: list[Block] – chain đã được convert từ dict
        """
        if not chain_list:
            return False

        # kiểm tra genesis khớp với genesis local
        if chain_list[0].hash != self.chain[0].hash:
            print("Genesis block không khớp.")
            return False

        for i in range(1, len(chain_list)):
            if not self.is_valid_new_block(chain_list[i], chain_list[i - 1]):
                return False

        return True


    def sync_chain(self, peers, add_log):
        """
        Lấy chain từ các peers, áp dụng quy tắc:
        - Chuỗi dài nhất, hợp lệ -> thay thế chain hiện tại.
        """
        max_length = len(self.chain)
        best_chain = None

        for peer in peers:
            try:
                res = requests.get(f"{peer}/chain", timeout=3)
                data = res.json()

                length = data.get("length")
                chain_data = data.get("chain")

                # dữ liệu không đầy đủ
                if length is None or chain_data is None:
                    continue

                if length > max_length:
                    # convert dict -> Block
                    candidate_chain = [Block.from_dict(b) for b in chain_data]

                    if self._validate_external_chain(candidate_chain):
                        max_length = length
                        best_chain = candidate_chain

            except Exception as e:
                add_log(f"Không thể sync chain từ {peer}: {e}")

        if best_chain:
            self.chain = best_chain
            self._notify()
            return True

        return False

    def get_balance(self, address):
        balance = 0

        for block in self.chain:
            for tx in block.transactions:
                # tiền nhận
                if tx.get("to") == address:
                    balance += float(tx.get("amount", 0))

                # tiền gửi
                if tx.get("from") == address:
                    balance -= float(tx.get("amount", 0))

        return balance


