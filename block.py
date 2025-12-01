import hashlib
import time


class Block:
    def __init__(self, index, timestamp, data, previous_hash, nonce=0, block_hash=None):
        # Số thứ tự của block trong chuỗi
        self.index = index

        # Thời gian tạo block (dùng time.time() hoặc chuỗi datetime)
        self.timestamp = timestamp

        # Dữ liệu chứa trong block (có thể là string, dict, v.v.)
        self.data = data

        # Hash của block trước đó trong chuỗi
        self.previous_hash = previous_hash

        # Nonce dùng cho Proof-of-Work
        self.nonce = nonce

        # Hash của block hiện tại
        # Nếu chưa truyền vào thì tự tính bằng calculate_hash()
        self.hash = block_hash or self.calculate_hash()

    def calculate_hash(self):
        """
        Tính hash SHA-256 cho block hiện tại.
        Ghép các trường: index + timestamp + data + previous_hash + nonce
        rồi đưa vào SHA-256.
        """
        raw_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()

    def mine(self, difficulty):
        """
        Proof-of-Work:
        Tăng nonce cho đến khi hash bắt đầu bằng '0' * difficulty.
        """
        target_prefix = "0" * difficulty

        # Lặp cho đến khi hash thỏa điều kiện difficulty
        while True:
            self.hash = self.calculate_hash()
            if self.hash.startswith(target_prefix):
                # Đã đào thành công
                # print(f"Block {self.index} mined: {self.hash}")
                break
            self.nonce += 1

    @staticmethod
    def create_genesis_block():
        """
        Tạo block đầu tiên trong chuỗi (genesis block).
        previous_hash có thể đặt là '0' * 64 (giống 64 hex zero).
        """
        return Block(
            index=0,
            timestamp=time.time(),
            data="Genesis Block",
            previous_hash="0" * 64
        )

    @staticmethod
    def create_block_from_previous(previous_block, data):
        """
        Tạo block mới dựa trên block trước đó:
        - index = previous_block.index + 1
        - previous_hash = previous_block.hash
        - timestamp = thời gian hiện tại
        - nonce = 0 (sau đó sẽ mine để tìm nonce đúng)
        """
        return Block(
            index=previous_block.index + 1,
            timestamp=time.time(),
            data=data,
            previous_hash=previous_block.hash,
            nonce=0
        )
