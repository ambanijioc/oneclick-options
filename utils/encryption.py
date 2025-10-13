"""
Encryption utilities for securing sensitive data like API secrets.
Uses Fernet symmetric encryption from cryptography library.
"""

from cryptography.fernet import Fernet, InvalidToken
from config import config
from logger import logger


def generate_key() -> str:
    """
    Generate a new Fernet encryption key.
    
    Returns:
        Base64-encoded encryption key as string
    """
    key = Fernet.generate_key()
    return key.decode()


def encrypt_secret(secret: str) -> str:
    """
    Encrypt a secret using Fernet encryption.
    
    Args:
        secret: Plain text secret to encrypt
    
    Returns:
        Encrypted secret as base64 string
    
    Raises:
        Exception: If encryption fails
    """
    try:
        fernet = config.encryption.get_fernet()
        encrypted = fernet.encrypt(secret.encode())
        
        logger.debug("[encryption.encrypt_secret] Secret encrypted successfully")
        return encrypted.decode()
        
    except Exception as e:
        logger.error(f"[encryption.encrypt_secret] Encryption failed: {e}")
        raise


def decrypt_secret(encrypted_secret: str) -> str:
    """
    Decrypt an encrypted secret.
    
    Args:
        encrypted_secret: Encrypted secret as base64 string
    
    Returns:
        Decrypted plain text secret
    
    Raises:
        InvalidToken: If decryption fails (wrong key or corrupted data)
    """
    try:
        fernet = config.encryption.get_fernet()
        decrypted = fernet.decrypt(encrypted_secret.encode())
        
        logger.debug("[encryption.decrypt_secret] Secret decrypted successfully")
        return decrypted.decode()
        
    except InvalidToken as e:
        logger.error(
            f"[encryption.decrypt_secret] Invalid token or key - "
            f"decryption failed: {e}"
        )
        raise
    except Exception as e:
        logger.error(f"[encryption.decrypt_secret] Decryption failed: {e}")
        raise


if __name__ == "__main__":
    # Test encryption/decryption
    print("Testing encryption utilities...")
    
    # Generate new key
    new_key = generate_key()
    print(f"Generated key: {new_key[:20]}...")
    
    # Test encrypt/decrypt
    test_secret = "my_super_secret_api_key_123"
    
    encrypted = encrypt_secret(test_secret)
    print(f"✅ Encrypted: {encrypted[:30]}...")
    
    decrypted = decrypt_secret(encrypted)
    print(f"✅ Decrypted: {decrypted}")
    
    assert test_secret == decrypted, "Encryption/decryption mismatch!"
    print("✅ Encryption test passed!")
  
