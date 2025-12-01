import hashlib
import time


class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        # Số thứ tự của block
        self.index = index

        # Thời gian tạo block (dùng time.time() – số giây)
        self.timestamp = timestamp

        # Dữ liệu lưu trong block (transaction, message, v.v.)
        self.data = data

        # Hash của block trước đó trong chuỗi
        self.previous_hash = previous_hash

        # Hash của block hiện tại (tự tính)
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """
        Tính hash SHA-256 từ các trường:
        index + timestamp + data + previous_hash
        """
        raw_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}"
        return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()


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


def demo():
    print("=== Demo Blockchain đơn giản ===")
    my_chain = Blockchain()

    # Thêm một vài block
    my_chain.add_block("A gửi B 10 coin")
    my_chain.add_block("B gửi C 5 coin")
    my_chain.add_block("C gửi D 1 coin")

    print("\n--- Nội dung blockchain ---")
    for block in my_chain.chain:
        print("-------------")
        print("Index      :", block.index)
        print("Timestamp  :", time.ctime(block.timestamp))
        print("Data       :", block.data)
        print("Prev Hash  :", block.previous_hash)
        print("Hash       :", block.hash)

    # Kiểm tra hợp lệ
    print("\nBlockchain hợp lệ?", my_chain.is_chain_valid())

    # Giả lập tấn công: sửa dữ liệu 1 block giữa
    print("\n>>> Giả lập sửa dữ liệu block 1...")
    my_chain.chain[1].data = "A gửi B 1000 coin"

    # Vẫn giữ nguyên hash cũ → chain phải invalid
    print("Blockchain hợp lệ sau khi sửa?", my_chain.is_chain_valid())


if __name__ == "__main__":
    demo()
