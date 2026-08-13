"""
Everything here just points to whatever was most recently uploaded or
produced. Restarting the server clears it.
"""


state = {
    "cover_image": None,  #the image the sender uploaded
    "key_image": None,  #the key image used to encrypt
    "coord": None,  #(x,y) tuple - secret coordinate
    "encrypted_image": None,  #output of encrypt_image
    "decrypted_image": None,  #output of decrypt_image; will be garbage if correct key is not used
}