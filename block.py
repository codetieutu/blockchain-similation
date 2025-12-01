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
