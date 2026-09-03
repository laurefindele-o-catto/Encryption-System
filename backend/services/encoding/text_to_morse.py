"""
Phase 2 stub: text -> Morse string (dots, dashes, intra/inter-letter
and inter-word gaps as a single flat string using sentinel characters).

NOT IMPLEMENTED in Phase 1. The signature is the planned Phase 2 contract.
"""

ITU_MORSE_TABLE = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',
    'E': '.',     'F': '..-.',  'G': '--.',   'H': '....',
    'I': '..',    'J': '.---',  'K': '-.-',   'L': '.-..',
    'M': '--',    'N': '-.',    'O': '---',   'P': '.--.',
    'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',
    'Y': '-.--',  'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    '.': '.-.-.-', ',': '--..--',	'?': '..--..',
}


def text_to_morse(text: str) -> str:
    """
    Convert plaintext into a standard ITU Morse string.

    Letters within a word are separated by a single space.
    Words are separated by ' / '.
    Characters not in ITU_MORSE_TABLE (and not plain spaces) are skipped.
    """
    words = text.upper().split(' ')
    encoded_words = []
    msg = "Converted to Morse"
    
    for word in words:
        letters = []
        for ch in word:
            if ch in ITU_MORSE_TABLE:
                letters.append(ITU_MORSE_TABLE[ch])
            else:
                msg = "Some letters were skipped."
        encoded_words.append(' '.join(letters))
        
    return '/'.join(encoded_words)