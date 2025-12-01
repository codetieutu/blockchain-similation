from block import Block
from blockChain import Blockchain
import time
import hashlib

def main():
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
        print("Timestamp  :", block.timestamp)
        print("Data       :", block.data)
        print("Prev Hash  :", block.previous_hash)
        print("Hash       :", block.hash)

    # Kiểm tra hợp lệ
    print("\nBlockchain hợp lệ?", my_chain.is_chain_valid())

    # Giả lập tấn công: sửa dữ liệu 1 block giữa
    print("\n>>> Giả lập sửa dữ liệu block 1...")
    my_chain.chain[1].data = "A gửi B 1000 coin"
    raw_string = f"{my_chain.chain[1].index}{my_chain.chain[1].timestamp}{my_chain.chain[1].data}{my_chain.chain[1].previous_hash}"
    my_chain.chain[1].hash = hashlib.sha256(raw_string.encode("utf-8")).hexdigest()

    # Vẫn giữ nguyên hash cũ → chain phải invalid
    print("Blockchain hợp lệ sau khi sửa?", my_chain.is_chain_valid())


if __name__ == "__main__":
    main()
