from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
import base64


def generate_key_pair():
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key


def encrypt_message(public_key_str, message):
    public_key = RSA.import_key(public_key_str)
    cipher = PKCS1_OAEP.new(public_key)

    # Ensure message is encoded in UTF-8
    encrypted_message = cipher.encrypt(message.encode('utf-8'))

    # Encode the encrypted message in base64 to avoid non-ASCII issues
    return base64.b64encode(encrypted_message).decode('utf-8')


def decrypt_message(private_key_str, encrypted_message):
    private_key = RSA.import_key(private_key_str)
    cipher = PKCS1_OAEP.new(private_key)

    # Decode the Base64-encoded message before decrypting
    encrypted_message_bytes = base64.b64decode(encrypted_message)

    # Decrypt the message and decode it from bytes to a string
    decrypted_message = cipher.decrypt(encrypted_message_bytes)

    return decrypted_message.decode('utf-8')  # Decode the decrypted bytes to a UTF-8 string

