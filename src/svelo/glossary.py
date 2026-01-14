"""Educational glossary for classical cryptography concepts."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class GlossaryEntry:
    """A cipher or encoding glossary entry."""
    name: str
    category: str
    description: str
    how_it_works: str
    historical_context: str
    security_level: str
    difficulty: str  # "Beginner [+]", "Intermediate [++]", or "Advanced [+++]"
    related_ciphers: List[str]
    references: List[str]


GLOSSARY: Dict[str, GlossaryEntry] = {
    "caesar": GlossaryEntry(
        name="Caesar Cipher",
        category="Substitution Cipher",
        description="A simple substitution cipher that shifts each letter by a fixed number of positions in the alphabet.",
        how_it_works="Each letter is replaced by a letter a fixed number of positions down the alphabet. For example, with a shift of 3, A becomes D, B becomes E, etc. The shift wraps around, so with shift 3, X becomes A, Y becomes B, Z becomes C.",
        historical_context="Named after Julius Caesar, who used it to protect military messages around 58 BC. The shift of 3 was his preferred setting. It's one of the oldest known ciphers in history.",
        security_level="Broken - easily defeated by frequency analysis or brute force (only 25 possible keys)",
        difficulty="Beginner [+]",
        related_ciphers=["rot13", "atbash", "substitution"],
        references=[
            "https://en.wikipedia.org/wiki/Caesar_cipher",
            "http://practicalcryptography.com/ciphers/caesar-cipher/",
        ],
    ),
    "vigenere": GlossaryEntry(
        name="Vigenère Cipher",
        category="Polyalphabetic Substitution Cipher",
        description="A method of encrypting text using a series of different Caesar ciphers based on the letters of a keyword.",
        how_it_works="Uses a keyword to determine shift amounts. Each letter of the keyword specifies a different Caesar shift. The keyword repeats to cover the entire message. For example, with key 'KEY', the first letter shifts by K(10), second by E(4), third by Y(24), then repeats.",
        historical_context="Invented by Giovan Battista Bellaso in 1553, but misattributed to Blaise de Vigenère in the 19th century. It was considered unbreakable for 300 years until Charles Babbage and Friedrich Kasiski independently broke it in the mid-1800s.",
        security_level="Broken - vulnerable to Kasiski examination and frequency analysis for repeated keys",
        difficulty="Intermediate [++]",
        related_ciphers=["beaufort", "variant", "autokey", "caesar"],
        references=[
            "https://en.wikipedia.org/wiki/Vigenère_cipher",
            "http://practicalcryptography.com/ciphers/vigenere-gronsfeld-and-autokey-cipher/",
        ],
    ),
    "beaufort": GlossaryEntry(
        name="Beaufort Cipher",
        category="Polyalphabetic Substitution Cipher",
        description="A reciprocal cipher similar to Vigenère, but using subtraction instead of addition.",
        how_it_works="Instead of adding the key value (like Vigenère), Beaufort subtracts the plaintext from the key: C = (K - P) mod 26. The cipher is reciprocal, meaning encryption and decryption use the same process.",
        historical_context="Named after Sir Francis Beaufort (famous for the Beaufort wind scale), though he may not have invented it. Used by some military organizations in the past.",
        security_level="Broken - similar weaknesses to Vigenère cipher",
        difficulty="Intermediate [++]",
        related_ciphers=["vigenere", "variant"],
        references=[
            "https://en.wikipedia.org/wiki/Beaufort_cipher",
            "http://practicalcryptography.com/ciphers/beaufort-cipher/",
        ],
    ),
    "playfair": GlossaryEntry(
        name="Playfair Cipher",
        category="Digraph Substitution Cipher",
        description="A manual symmetric encryption technique that encrypts pairs of letters (digraphs) using a 5×5 grid of letters.",
        how_it_works="Creates a 5×5 grid from a keyword (J and I share a cell). Plaintext is split into letter pairs. Each pair is encrypted based on their positions in the grid: same row shifts right, same column shifts down, different row/column swaps corners.",
        historical_context="Invented by Charles Wheatstone in 1854, but promoted by Lord Playfair. Used by the British military in the Boer War and WWI. First literal digraph substitution cipher to be used in practice.",
        security_level="Broken - but significantly harder to break than simple substitution; requires more sophisticated cryptanalysis",
        difficulty="Advanced [+++]",
        related_ciphers=["four-square", "two-square", "hill"],
        references=[
            "https://en.wikipedia.org/wiki/Playfair_cipher",
            "http://practicalcryptography.com/ciphers/playfair-cipher/",
        ],
    ),
    "hill": GlossaryEntry(
        name="Hill Cipher",
        category="Polygraphic Substitution Cipher",
        description="A polygraphic substitution cipher based on linear algebra, using matrix multiplication.",
        how_it_works="Groups plaintext into blocks (this implementation uses 2×2 matrices). Each block is multiplied by a key matrix modulo 26. Decryption uses the modular inverse of the key matrix.",
        historical_context="Invented by Lester S. Hill in 1929. One of the first practical polygraphic ciphers and the first cipher that could operate on more than three symbols at once. Still studied in linear algebra courses.",
        security_level="Broken - vulnerable to known-plaintext attacks",
        difficulty="Advanced [+++]",
        related_ciphers=["playfair", "affine"],
        references=[
            "https://en.wikipedia.org/wiki/Hill_cipher",
            "http://practicalcryptography.com/ciphers/hill-cipher/",
        ],
    ),
    "railfence": GlossaryEntry(
        name="Rail Fence Cipher",
        category="Transposition Cipher",
        description="A transposition cipher that writes the message in a zigzag pattern across multiple 'rails', then reads off the rows.",
        how_it_works="The message is written diagonally downwards and upwards alternately across a number of 'rails'. After reaching the bottom rail, direction reverses to go upward. The ciphertext is created by reading off each rail in sequence.",
        historical_context="One of the simplest transposition ciphers. Used in various forms throughout history, though less common in serious cryptography. Often used as a teaching example of transposition.",
        security_level="Broken - easily defeated by trying different numbers of rails (small key space)",
        difficulty="Intermediate [++]",
        related_ciphers=["columnar", "scytale"],
        references=[
            "https://en.wikipedia.org/wiki/Rail_fence_cipher",
            "http://practicalcryptography.com/ciphers/rail-fence-cipher/",
        ],
    ),
    "columnar": GlossaryEntry(
        name="Columnar Transposition",
        category="Transposition Cipher",
        description="A transposition cipher that rearranges the plaintext by writing it into a grid row-by-row and reading it column-by-column in a specific order.",
        how_it_works="The plaintext is written into rows of fixed width. The columns are then read off in an order determined by a keyword (alphabetically sorted). This rearranges the letters without substituting them.",
        historical_context="Used extensively in military communications before modern cryptography. Often combined with substitution ciphers for added security. A simple and practical manual cipher.",
        security_level="Broken - vulnerable to pattern analysis and brute force",
        difficulty="Intermediate [++]",
        related_ciphers=["railfence", "scytale", "adfgx"],
        references=[
            "https://en.wikipedia.org/wiki/Transposition_cipher",
            "http://practicalcryptography.com/ciphers/columnar-transposition-cipher/",
        ],
    ),
    "adfgx": GlossaryEntry(
        name="ADFGX Cipher",
        category="Fractionating Transposition Cipher",
        description="A field cipher used by the German Army during WWI that combines substitution and transposition using a 5×5 Polybius square.",
        how_it_works="Two-stage process: (1) Substitutes each letter with two letters from 'ADFGX' using a 5×5 grid, (2) applies columnar transposition to the result. The letters ADFGX were chosen because they are distinct in Morse code.",
        historical_context="Invented by Colonel Fritz Nebel in March 1918. Used during WWI's German Spring Offensive. Broken by French cryptanalyst Georges Painvin in April 1918 after intensive work. The break had significant military impact.",
        security_level="Broken - but was very secure for its time and difficult to break manually",
        difficulty="Advanced [+++]",
        related_ciphers=["adfgvx", "columnar", "polybius"],
        references=[
            "https://en.wikipedia.org/wiki/ADFGVX_cipher",
            "http://practicalcryptography.com/ciphers/adfgx-cipher/",
        ],
    ),
    "adfgvx": GlossaryEntry(
        name="ADFGVX Cipher",
        category="Fractionating Transposition Cipher",
        description="An extension of ADFGX that uses a 6×6 grid to support both letters and digits.",
        how_it_works="Like ADFGX but with a 6×6 Polybius square using letters 'ADFGVX'. This allows encryption of 36 characters (26 letters + 10 digits). Otherwise identical to ADFGX: substitution via grid, then columnar transposition.",
        historical_context="Introduced in June 1918 as an extension of ADFGX to include digits. Used in the final months of WWI. The extra complexity made cryptanalysis even harder.",
        security_level="Broken - similar weaknesses to ADFGX but more complex",
        difficulty="Advanced [+++]",
        related_ciphers=["adfgx", "columnar", "polybius"],
        references=[
            "https://en.wikipedia.org/wiki/ADFGVX_cipher",
            "http://practicalcryptography.com/ciphers/adfgvx-cipher/",
        ],
    ),
    "atbash": GlossaryEntry(
        name="Atbash Cipher",
        category="Substitution Cipher",
        description="A simple substitution cipher that replaces each letter with its reverse in the alphabet (A↔Z, B↔Y, etc.).",
        how_it_works="Each letter is replaced with the letter that is the same distance from the opposite end of the alphabet. A becomes Z, B becomes Y, C becomes X, and so on. The cipher is reciprocal (encryption = decryption).",
        historical_context="Originally used for the Hebrew alphabet around 500-600 BCE. The name comes from the first, last, second, and second-to-last letters of the Hebrew alphabet (Aleph-Taw-Beth-Shin). Found in the Bible (Jeremiah 25:26).",
        security_level="Broken - trivially broken; only one possible key",
        difficulty="Beginner [+]",
        related_ciphers=["caesar", "rot13", "reverse"],
        references=[
            "https://en.wikipedia.org/wiki/Atbash",
            "http://practicalcryptography.com/ciphers/atbash-cipher-cipher/",
        ],
    ),
    "rot13": GlossaryEntry(
        name="ROT13",
        category="Substitution Cipher",
        description="A Caesar cipher with a fixed shift of 13, making it self-reciprocal.",
        how_it_works="Each letter is replaced by the letter 13 positions after it in the alphabet. Since the alphabet has 26 letters, applying ROT13 twice returns the original text (13 + 13 = 26 = 0 mod 26).",
        historical_context="Originated in early internet forums (Usenet) around 1980s as a way to hide spoilers, punchlines, or potentially offensive content without actual encryption. Still used today for trivial obfuscation.",
        security_level="Not secure - trivial obfuscation only; decryption is identical to encryption",
        difficulty="Beginner [+]",
        related_ciphers=["caesar", "atbash"],
        references=[
            "https://en.wikipedia.org/wiki/ROT13",
        ],
    ),
    "morse": GlossaryEntry(
        name="Morse Code",
        category="Encoding (not encryption)",
        description="A character encoding scheme that represents letters and numbers as sequences of dots and dashes.",
        how_it_works="Each letter and number is represented by a unique sequence of short signals (dots) and long signals (dashes). Originally designed for transmission over telegraph lines. Not encryption - just encoding.",
        historical_context="Developed by Samuel Morse and Alfred Vail in the 1830s-1840s for use with the telegraph. Revolutionized long-distance communication. Still used in aviation, amateur radio, and assistive technology.",
        security_level="Not encryption - provides no security, only encoding",
        difficulty="Beginner [+]",
        related_ciphers=["bacon", "binary"],
        references=[
            "https://en.wikipedia.org/wiki/Morse_code",
        ],
    ),
    "base64": GlossaryEntry(
        name="Base64",
        category="Encoding (not encryption)",
        description="An encoding scheme that represents binary data using 64 ASCII characters, designed for safe transmission over text-based protocols.",
        how_it_works="Converts binary data into a set of 64 printable ASCII characters (A-Z, a-z, 0-9, +, /). Every 3 bytes (24 bits) are encoded as 4 characters (6 bits each). Used to encode binary data in email, URLs, and data transfer.",
        historical_context="Defined in RFC 4648. Widely used in MIME email encoding, data URLs, and API authentication tokens (like JWT). Essential for embedding binary data in text formats.",
        security_level="Not encryption - provides no security; easily reversible encoding",
        difficulty="Intermediate [++]",
        related_ciphers=["base32", "base58", "hex"],
        references=[
            "https://en.wikipedia.org/wiki/Base64",
            "https://datatracker.ietf.org/doc/html/rfc4648",
        ],
    ),
    "autokey": GlossaryEntry(
        name="Autokey Cipher",
        category="Polyalphabetic Substitution Cipher",
        description="An improvement on the Vigenère cipher that uses the plaintext itself as part of the key to avoid key repetition.",
        how_it_works="Starts with a short key (priming key), then uses the plaintext letters as the key for subsequent letters. This eliminates the repeating key pattern that makes Vigenère vulnerable to Kasiski examination.",
        historical_context="Invented by Blaise de Vigenère in 1586 (this was actually Vigenère's invention, not the cipher that bears his name). Largely forgotten until the 19th century when it was rediscovered.",
        security_level="Broken - but more secure than standard Vigenère; vulnerable to known-plaintext attacks",
        difficulty="Intermediate [++]",
        related_ciphers=["vigenere", "beaufort"],
        references=[
            "https://en.wikipedia.org/wiki/Autokey_cipher",
            "http://practicalcryptography.com/ciphers/autokey-cipher/",
        ],
    ),
    "variant": GlossaryEntry(
        name="Variant Beaufort Cipher",
        category="Polyalphabetic Substitution Cipher",
        description="A variant of the Beaufort cipher that uses a different formula, making it non-reciprocal.",
        how_it_works="Uses the formula C = (P - K) mod 26 for encryption and P = (K + C) mod 26 for decryption, unlike standard Beaufort which is reciprocal. Functionally similar to Vigenère but with subtraction instead of addition.",
        historical_context="A variation of the standard Beaufort cipher. The distinction between Beaufort and Variant Beaufort can cause confusion in literature, as different sources sometimes use opposite definitions.",
        security_level="Broken - similar weaknesses to Vigenère and standard Beaufort ciphers",
        difficulty="Intermediate [++]",
        related_ciphers=["beaufort", "vigenere"],
        references=[
            "https://en.wikipedia.org/wiki/Beaufort_cipher",
            "https://www.dcode.fr/variant-beaufort-cipher",
        ],
    ),
    "polybius": GlossaryEntry(
        name="Polybius Square",
        category="Substitution Cipher",
        description="An ancient cipher that encodes letters as coordinate pairs using a 5×5 grid, allowing letters to be represented by numbers.",
        how_it_works="Letters are arranged in a 5×5 grid (I and J typically share a cell). Each letter is encoded as two digits representing its row and column coordinates. For example, if H is at position (2,3), it encodes as '23'.",
        historical_context="Invented by the ancient Greek historian Polybius around 150 BCE. Originally designed for signaling with torches - one set for rows, another for columns. Forms the basis for later ciphers like ADFGX/ADFGVX.",
        security_level="Broken - provides minimal security; mainly historical and educational interest",
        difficulty="Intermediate [++]",
        related_ciphers=["adfgx", "adfgvx"],
        references=[
            "https://en.wikipedia.org/wiki/Polybius_square",
            "http://practicalcryptography.com/ciphers/polybius-square-cipher/",
        ],
    ),
    "scytale": GlossaryEntry(
        name="Scytale Cipher",
        category="Transposition Cipher",
        description="One of the earliest known transposition ciphers, using a cylindrical tool to rearrange message letters.",
        how_it_works="A strip of material is wrapped around a rod of specific diameter. The message is written lengthwise down the rod. When unwrapped, the letters appear scrambled. To decrypt, the recipient wraps the strip around a rod of the same diameter.",
        historical_context="Used by ancient Spartans around 400 BCE for military communications. One of the oldest known encryption devices. The scytale is mentioned by Plutarch and other ancient historians as a Spartan military tool.",
        security_level="Broken - trivial by modern standards; historical significance only",
        difficulty="Intermediate [++]",
        related_ciphers=["columnar", "railfence"],
        references=[
            "https://en.wikipedia.org/wiki/Scytale",
            "https://www.dcode.fr/scytale-cipher",
        ],
    ),
    "bacon": GlossaryEntry(
        name="Bacon Cipher",
        category="Substitution Cipher",
        description="A steganographic cipher that encodes letters as sequences of two distinct symbols (A and B), representing a 5-bit binary encoding.",
        how_it_works="Each letter is encoded as a 5-character sequence of A's and B's. Two variants exist: the original 24-letter version (I/J and U/V combined) and a 26-letter binary version. The cipher can be hidden in text by using two different fonts or styles.",
        historical_context="Devised by Francis Bacon in 1605. Designed to hide messages in innocent-looking text using two typefaces or writing styles. One of the earliest examples of steganography combined with a cipher.",
        security_level="Broken - but interesting for steganographic applications",
        difficulty="Intermediate [++]",
        related_ciphers=["binary", "morse"],
        references=[
            "https://en.wikipedia.org/wiki/Bacon%27s_cipher",
            "http://practicalcryptography.com/ciphers/baconian-cipher/",
        ],
    ),
    "keyword": GlossaryEntry(
        name="Keyword Substitution Cipher",
        category="Monoalphabetic Substitution Cipher",
        description="A substitution cipher where the cipher alphabet is created from a keyword, providing a simple keyed alternative to random substitution.",
        how_it_works="A keyword is used to create the cipher alphabet by removing duplicate letters, then appending the remaining alphabet letters. For example, keyword 'ZEBRA' creates cipher alphabet 'ZEBRACIJKLMNOPQSTUVWXY', mapping A→Z, B→E, C→B, etc.",
        historical_context="A simplified form of general monoalphabetic substitution. Easier to remember than random substitution alphabets, making it practical for manual use. Commonly taught in basic cryptography courses.",
        security_level="Broken - vulnerable to frequency analysis like all monoalphabetic substitution ciphers",
        difficulty="Intermediate [++]",
        related_ciphers=["caesar", "atbash"],
        references=[
            "https://en.wikipedia.org/wiki/Substitution_cipher#Simple_substitution",
            "http://practicalcryptography.com/ciphers/simple-substitution-cipher/",
        ],
    ),
    "hex": GlossaryEntry(
        name="Hexadecimal",
        category="Encoding (not encryption)",
        description="A base-16 number system using digits 0-9 and letters A-F, commonly used to represent binary data in a human-readable format.",
        how_it_works="Each byte (8 bits) is represented as two hexadecimal digits (0-9, A-F). For example, the letter 'A' (ASCII 65, binary 01000001) is represented as '41' in hex. Widely used in computing for memory addresses, color codes, and binary data representation.",
        historical_context="Hexadecimal notation has been used since the 1960s in computing. It provides a compact way to represent binary data that's more readable than binary but maintains a direct relationship with the underlying bits (each hex digit = 4 bits).",
        security_level="Not encryption - provides no security; simple encoding",
        difficulty="Beginner [+]",
        related_ciphers=["binary", "base64"],
        references=[
            "https://en.wikipedia.org/wiki/Hexadecimal",
        ],
    ),
    "binary": GlossaryEntry(
        name="Binary",
        category="Encoding (not encryption)",
        description="A base-2 number system using only 0s and 1s, the fundamental language of computers.",
        how_it_works="Each character is represented as a sequence of 8 bits (1 byte). For example, 'A' is 01000001. Binary is how computers internally store all data, though it's verbose for human reading.",
        historical_context="Binary arithmetic was developed by Gottfried Leibniz in 1679, but binary became fundamental to computing in the 20th century with the development of digital computers. All digital data is ultimately stored and processed as binary.",
        security_level="Not encryption - provides no security; simple encoding",
        difficulty="Beginner [+]",
        related_ciphers=["hex", "morse"],
        references=[
            "https://en.wikipedia.org/wiki/Binary_number",
        ],
    ),
    "base64url": GlossaryEntry(
        name="Base64url",
        category="Encoding (not encryption)",
        description="A URL-safe variant of Base64 that replaces problematic characters to allow safe use in URLs and filenames.",
        how_it_works="Like Base64, but uses '-' instead of '+', '_' instead of '/', and omits padding '=' characters (or makes them optional). This prevents issues when the encoded data appears in URLs or filenames where certain characters have special meaning.",
        historical_context="Defined in RFC 4648 as a URL and filename safe variant of Base64. Commonly used in web tokens (JWT), URL parameters, and anywhere Base64 data needs to be part of a URL.",
        security_level="Not encryption - provides no security; easily reversible encoding",
        difficulty="Intermediate [++]",
        related_ciphers=["base64", "base32", "url"],
        references=[
            "https://en.wikipedia.org/wiki/Base64#URL_applications",
            "https://datatracker.ietf.org/doc/html/rfc4648#section-5",
        ],
    ),
    "base32": GlossaryEntry(
        name="Base32",
        category="Encoding (not encryption)",
        description="A base-32 encoding using only uppercase letters A-Z and digits 2-7, designed to avoid ambiguous characters.",
        how_it_works="Encodes binary data using 32 ASCII characters (A-Z, 2-7), avoiding 0/O and 1/I/L confusion. Every 5 bytes (40 bits) becomes 8 characters (5 bits each). More verbose than Base64 but less error-prone when read by humans.",
        historical_context="Defined in RFC 4648. Used in systems where case-insensitivity or human readability is important, such as TOTP authentication codes, some file-sharing networks, and domain names.",
        security_level="Not encryption - provides no security; easily reversible encoding",
        difficulty="Intermediate [++]",
        related_ciphers=["base64", "base58"],
        references=[
            "https://en.wikipedia.org/wiki/Base32",
            "https://datatracker.ietf.org/doc/html/rfc4648#section-6",
        ],
    ),
    "base85": GlossaryEntry(
        name="Base85 (Ascii85)",
        category="Encoding (not encryption)",
        description="A base-85 encoding that's more space-efficient than Base64, encoding 4 bytes as 5 ASCII characters.",
        how_it_works="Encodes every 4 bytes (32 bits) as 5 characters using 85 printable ASCII characters. About 25% more efficient than Base64. Multiple variants exist: Adobe's Ascii85 (used in PostScript) and RFC 1924's version.",
        historical_context="Ascii85 was developed by Adobe for PostScript and PDF files to efficiently encode binary data. RFC 1924's variant (sometimes called 'btoa') is used in other applications. More compact than Base64 but less universally supported.",
        security_level="Not encryption - provides no security; easily reversible encoding",
        difficulty="Intermediate [++]",
        related_ciphers=["base64", "ascii85"],
        references=[
            "https://en.wikipedia.org/wiki/Ascii85",
            "https://datatracker.ietf.org/doc/html/rfc1924",
        ],
    ),
    "ascii85": GlossaryEntry(
        name="Ascii85",
        category="Encoding (not encryption)",
        description="Adobe's base-85 encoding variant using delimiters <~ and ~>, commonly used in PostScript and PDF files.",
        how_it_works="Identical to base85 but wraps encoded data in <~ ~> delimiters and uses Adobe's specific character set. Encodes 4 bytes as 5 characters. Special case: four zero bytes encode as 'z' for compression.",
        historical_context="Created by Adobe for PostScript Level 2 in 1992, later adopted in PDF. The 'z' compression feature makes it particularly efficient for data with zero-filled regions.",
        security_level="Not encryption - provides no security; easily reversible encoding",
        difficulty="Intermediate [++]",
        related_ciphers=["base85", "base64"],
        references=[
            "https://en.wikipedia.org/wiki/Ascii85",
        ],
    ),
    "base58": GlossaryEntry(
        name="Base58",
        category="Encoding (not encryption)",
        description="A base-58 encoding that omits ambiguous characters (0, O, I, l) for human-friendly readability, popularized by Bitcoin.",
        how_it_works="Uses 58 alphanumeric characters, excluding 0, O, I, and l to prevent visual confusion. Commonly used in cryptocurrency addresses, IPFS hashes, and other systems where humans need to read/transcribe encoded data. No padding characters.",
        historical_context="Invented by Satoshi Nakamoto for Bitcoin addresses in 2009. Designed to be compact like Base64 but avoid characters that look similar in many fonts, reducing transcription errors.",
        security_level="Not encryption - provides no security; easily reversible encoding",
        difficulty="Intermediate [++]",
        related_ciphers=["base64", "base32"],
        references=[
            "https://en.wikipedia.org/wiki/Binary-to-text_encoding#Base58",
        ],
    ),
    "url": GlossaryEntry(
        name="URL Encoding (Percent Encoding)",
        category="Encoding (not encryption)",
        description="Encodes special characters in URLs by replacing them with '%' followed by their hexadecimal ASCII value.",
        how_it_works="Characters that have special meaning in URLs (like spaces, &, =, ?) or non-ASCII characters are encoded as '%XX' where XX is the hex value. For example, space becomes '%20', '&' becomes '%26'. Required for safe transmission of data in URLs.",
        historical_context="Defined in RFC 3986 as part of the URI specification. Essential for web browsers and HTTP to safely transmit arbitrary data in URLs. Used billions of times daily in web requests.",
        security_level="Not encryption - provides no security; simple encoding for safe URL transmission",
        difficulty="Beginner [+]",
        related_ciphers=["hex", "base64url"],
        references=[
            "https://en.wikipedia.org/wiki/Percent-encoding",
            "https://datatracker.ietf.org/doc/html/rfc3986#section-2.1",
        ],
    ),
    "fibonacci": GlossaryEntry(
        name="Fibonacci Cipher",
        category="Polyalphabetic Substitution Cipher",
        description="A variant cipher that uses the Fibonacci sequence (0,1,1,2,3,5,8...) to determine shifting amounts.",
        how_it_works="Each letter is shifted by the current Fibonacci number. The sequence starts with two seed values (often 0,1) and each subsequent shift is the sum of the previous two: 0+1=1, 1+1=2, 1+2=3, 2+3=5, etc. Can advance on letters only or all characters.",
        historical_context="A modern variant cipher created for educational purposes, combining the famous Fibonacci sequence with classical shift cipher techniques. Not historically used, but demonstrates how mathematical sequences can create variable shift patterns.",
        security_level="Broken - predictable shift pattern based on well-known sequence; vulnerable to frequency analysis",
        difficulty="Intermediate [++]",
        related_ciphers=["vigenere", "caesar"],
        references=[
            "https://en.wikipedia.org/wiki/Fibonacci_number",
        ],
    ),
    "reverse": GlossaryEntry(
        name="Reverse Text",
        category="Simple Transformation (not encryption)",
        description="Reverses the order of characters in the text, reading backwards from end to start.",
        how_it_works="Simply reverses the entire string character by character. 'HELLO' becomes 'OLLEH'. Sometimes used in combination with other ciphers or as a simple obfuscation technique.",
        historical_context="Not a historical cipher but a basic text transformation. Sometimes seen in puzzles, recreational cryptography, or as a weak obfuscation layer. Occasionally combined with other techniques.",
        security_level="Not secure - trivial to recognize and reverse",
        difficulty="Beginner [+]",
        related_ciphers=["atbash"],
        references=[
            "https://en.wikipedia.org/wiki/Reverse_text",
        ],
    ),
    "xor": GlossaryEntry(
        name="XOR Cipher",
        category="Stream Cipher",
        description="A cipher that applies the XOR (exclusive OR) operation between plaintext and a key, byte by byte.",
        how_it_works="Each byte of plaintext is XORed with a key byte. With single-byte XOR, the same key byte is used for all data. Multi-byte XOR repeats a key sequence. XOR is reversible: plaintext XOR key = ciphertext, ciphertext XOR key = plaintext.",
        historical_context="XOR is fundamental to modern cryptography and used in stream ciphers, one-time pads (OTP), and block cipher modes. Single-byte XOR is weak and easily broken by frequency analysis, but XOR with a truly random key (OTP) is theoretically unbreakable.",
        security_level="Single-byte: Broken (easily brute-forced); Multi-byte: Weak; One-time pad: Unbreakable (if key is truly random and never reused)",
        difficulty="Intermediate [++]",
        related_ciphers=["vigenere"],
        references=[
            "https://en.wikipedia.org/wiki/XOR_cipher",
        ],
    ),
    "gzip": GlossaryEntry(
        name="Gzip Compression",
        category="Compression (not encryption)",
        description="A popular data compression format based on the DEFLATE algorithm, widely used for file compression and web content.",
        how_it_works="Uses the DEFLATE algorithm (combination of LZ77 and Huffman coding) to compress data. Includes headers with metadata and CRC checksums. Lossless compression - decompressed data is identical to original.",
        historical_context="Created by Jean-loup Gailly and Mark Adler in 1992 as a free replacement for the patented 'compress' utility. Became standard for web content compression (Content-Encoding: gzip) and is used in countless applications.",
        security_level="Not encryption - provides no security; compression only",
        difficulty="Intermediate [++]",
        related_ciphers=["zlib"],
        references=[
            "https://en.wikipedia.org/wiki/Gzip",
            "https://datatracker.ietf.org/doc/html/rfc1952",
        ],
    ),
    "zlib": GlossaryEntry(
        name="Zlib Compression",
        category="Compression (not encryption)",
        description="A compression library and format using DEFLATE algorithm, similar to gzip but with different headers.",
        how_it_works="Uses the same DEFLATE compression as gzip but with simpler headers (2-byte header vs gzip's 10-byte header). Often used in protocols and file formats where the metadata is handled separately.",
        historical_context="Developed by Jean-loup Gailly and Mark Adler. Specified in RFC 1950. Used internally by PNG images, Git, and many network protocols. More lightweight than gzip for embedded compression.",
        security_level="Not encryption - provides no security; compression only",
        difficulty="Intermediate [++]",
        related_ciphers=["gzip"],
        references=[
            "https://en.wikipedia.org/wiki/Zlib",
            "https://datatracker.ietf.org/doc/html/rfc1950",
        ],
    ),
    "jwt": GlossaryEntry(
        name="JWT (JSON Web Token)",
        category="Encoding (not encryption)",
        description="A compact, URL-safe token format for securely transmitting JSON data, commonly used for authentication and authorization.",
        how_it_works="Three parts separated by dots: header.payload.signature. Header and payload are Base64url-encoded JSON. Signature verifies integrity using HMAC, RSA, or ECDSA. The decoder extracts and decodes the JSON parts without signature verification.",
        historical_context="Defined in RFC 7519 (2015). Became the standard for web authentication tokens, used extensively in OAuth 2.0, OpenID Connect, and API authentication. Allows stateless authentication without server-side sessions.",
        security_level="Not encryption - payload is readable (only Base64url encoded). Security comes from signature verification, not obscurity.",
        difficulty="Intermediate [++]",
        related_ciphers=["base64url"],
        references=[
            "https://en.wikipedia.org/wiki/JSON_Web_Token",
            "https://datatracker.ietf.org/doc/html/rfc7519",
        ],
    ),
}


def get_entry(cipher_name: str) -> Optional[GlossaryEntry]:
    """Get glossary entry for a cipher."""
    return GLOSSARY.get(cipher_name.lower())


def get_all_entries() -> List[GlossaryEntry]:
    """Get all glossary entries sorted by name."""
    return sorted(GLOSSARY.values(), key=lambda e: e.name)


def search_entries(query: str) -> List[GlossaryEntry]:
    """Search glossary entries by name, category, or description."""
    query_lower = query.lower()
    results = []
    for entry in GLOSSARY.values():
        if (query_lower in entry.name.lower() or
            query_lower in entry.category.lower() or
            query_lower in entry.description.lower()):
            results.append(entry)
    return sorted(results, key=lambda e: e.name)

def difficulty_symbol(difficulty: str) -> str:
    """Convert difficulty level to a visual symbol."""
    difficulty_map = {
        "Beginner [+]": "[+]",
        "Intermediate [++]": "[++]",
        "Advanced [+++]": "[+++]",
    }
    return difficulty_map.get(difficulty, "[?]")


def format_entry(entry: GlossaryEntry, show_full: bool = True) -> str:
    """Format a glossary entry for display."""
    lines = [
        f"\n{entry.name}",
        "=" * len(entry.name),
        f"\nCategory: {entry.category}",
        f"Difficulty: {entry.difficulty}",
        f"\n{entry.description}",
    ]

    if show_full:
        lines.extend([
            f"\nHow it works:",
            f"  {entry.how_it_works}",
            f"\nHistorical context:",
            f"  {entry.historical_context}",
            f"\nSecurity: {entry.security_level}",
        ])

        if entry.related_ciphers:
            lines.append(f"\nRelated: {', '.join(entry.related_ciphers)}")

        if entry.references:
            lines.append("\nLearn more:")
            for ref in entry.references:
                lines.append(f"  • {ref}")

    return "\n".join(lines)
