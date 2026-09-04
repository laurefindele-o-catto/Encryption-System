"""
Per-frame key derivation.

The analysis report flagged sequential seeds (base_seed + N) as a
vulnerability: recovering one frame's key reveals every other key via a
fixed linear offset. This replaces that with a one-way hash, so knowing
key_5 reveals nothing about key_6.
"""

import hashlib
import hmac


def derive_password_key(
    password: str,
    salt: bytes,
) -> bytes:
    #take receiver's pw, use a pw KDF and return fixed-length secret byte
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt = salt, 
        n=2**14,
        r=8,
        p=1,
        dklen = 32,
    )


def derive_master_key(
    password_key: bytes,
    secret_image_digest: bytes,
) -> bytes:
    # Combine the password-derived key and the one secret image into a master key.
    material = (
        b"DRPE-MASTER-v1"
        + password_key
        + secret_image_digest
    )
    
    return hashlib.sha256(material).digest()

def derive_frame_key(
    master_key: bytes,
    message_id: str,
    frame_index: int,
    purpose: bytes,
) -> bytes:
    #give each frame a different mask
    context = (
        b"DRPE-v1"
        + purpose
        + message_id.encode("utf-8")
        + frame_index.to_bytes(8, "big")
    )
    
    return hmac.new(
        master_key,
        context,
        hashlib.sha256,
    ).digest()
    
    
def derive_image_password_keys(
    password: str,
    salt: bytes,
    secret_image_digest: bytes,
    message_id: str,
    frame_index: int,
) -> tuple[bytes, bytes]:
    #return the p1, p2 masks for each image i.e each frame
    
    password_key = derive_password_key(password, salt)
    master_key = derive_master_key(password_key, secret_image_digest)
    
    p1_material = derive_frame_key(
        master_key, message_id, frame_index, b"DRPE/P1",
    )
    
    p2_material = derive_frame_key(
        master_key, message_id, frame_index, b"DRPE/P2",
    )
    
    return p1_material, p2_material