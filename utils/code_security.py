import hashlib
import os
from cryptography.fernet import Fernet
import time
import sys
from pathlib import Path

class CodeSecurity:
    def __init__(self):
        self.key_file = os.path.join(os.path.dirname(__file__), '../config/code_security.key')
        self.hash_file = os.path.join(os.path.dirname(__file__), '../config/code_hashes.txt')
        self._initialize_security()

    def _initialize_security(self):
        # Create key if it doesn't exist
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
            with open(self.key_file, 'wb') as f:
                f.write(key)

        # Load the encryption key
        with open(self.key_file, 'rb') as f:
            self.key = f.read()
        self.cipher_suite = Fernet(self.key)

    def encrypt_file(self, file_path):
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Encrypt the file data
        encrypted_data = self.cipher_suite.encrypt(file_data)
        
        # Save encrypted data
        with open(file_path + '.encrypted', 'wb') as f:
            f.write(encrypted_data)

    def decrypt_file(self, encrypted_file_path):
        try:
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt the file data
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            # Remove '.encrypted' from the path for the original file
            original_file = encrypted_file_path.replace('.encrypted', '')
            
            with open(original_file, 'wb') as f:
                f.write(decrypted_data)
        except Exception as e:
            print(f"Error decrypting file: {e}")
            sys.exit(1)

    def calculate_file_hash(self, file_path):
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def store_file_hash(self, file_path):
        """Store the hash of a file"""
        file_hash = self.calculate_file_hash(file_path)
        os.makedirs(os.path.dirname(self.hash_file), exist_ok=True)
        with open(self.hash_file, 'a') as f:
            f.write(f"{file_path}:{file_hash}\n")

    def verify_file_integrity(self, file_path):
        """Verify if a file has been modified"""
        current_hash = self.calculate_file_hash(file_path)
        
        # Initialize hash file if it doesn't exist
        if not os.path.exists(self.hash_file):
            self.store_file_hash(file_path)
            return True
            
        # Read existing hashes
        found = False
        with open(self.hash_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                stored_path, stored_hash = line.strip().split(':')
                if stored_path == file_path:
                    found = True
                    if stored_hash != current_hash:
                        raise SecurityException(f"File integrity check failed for {file_path}")
        
        # If file hash not found, store it
        if not found:
            self.store_file_hash(file_path)
        return True

class SecurityException(Exception):
    pass
