from block import Block
import time
class Blockchain:
    def __init__(self):
        # Khởi tạo chain với 1 genesis block
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        """
        Tạo block đầu tiên (genesis block).
        previous_hash có thể là "0" (hoặc chuỗi toàn số 0).
        """
        return Block(
            index=0,
            timestamp=time.time(),
            data="Genesis Block",
            previous_hash="0"
        )

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data):
        """
        Tạo block mới dựa trên block cuối cùng,
        rồi thêm vào chain.
        """
        previous_block = self.get_latest_block()
        new_block = Block(
            index=previous_block.index + 1,
            timestamp=time.time(),
            data=data,
            previous_hash=previous_block.hash
        )
        self.chain.append(new_block)

    def is_chain_valid(self):
        """
        Kiểm tra tính hợp lệ của toàn bộ blockchain:
        - Hash của từng block có đúng với calculate_hash không?
        - previous_hash của block hiện tại khớp với hash của block trước đó không?
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Kiểm tra hash hiện tại
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ Hash của block {i} không hợp lệ")
                return False

            # Kiểm tra previous_hash
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ previous_hash của block {i} không khớp block {i-1}")
                return False

        return True
