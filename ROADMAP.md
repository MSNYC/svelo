# Svelo Development Roadmap

This roadmap outlines the vision for growing Svelo from a practical decoding CLI into a comprehensive educational platform for cryptography.

## Core Philosophy

- **Educational First**: Every feature should help users learn
- **Stdlib Only**: Keep dependencies minimal for security and simplicity
- **Interactive Learning**: Make cryptography accessible and engaging
- **Historical Context**: Connect ciphers to their real-world usage

---

## Phase 1: Enhanced Educational Content (Current Focus)

### Glossary System
**Status**: ✅ Completed

A built-in glossary to explain cryptographic concepts, accessible from the CLI and interactive menu.

**Implemented Features:**
- ✅ CLI command: `svelo --info <cipher>` to view detailed glossary entries
- ✅ Interactive "Learn" menu (main menu option 5) with browse and search
- ✅ 33 comprehensive cipher entries covering all decoders and keyed ciphers
- ✅ Each entry includes: description, how it works, historical context, security level, related ciphers, and verified reference links
- ✅ Numbered selection for easy browsing
- ✅ Search functionality by name, category, or keyword
- ✅ All reference links verified and working

**Example:**
```bash
svelo --info vigenere
# Vigenère Cipher
# ===============
#
# Category: Polyalphabetic Substitution Cipher
#
# A method of encrypting text using a series of different Caesar ciphers
# based on the letters of a keyword.
#
# How it works:
#   Uses a keyword to determine shift amounts. Each letter of the keyword
#   specifies a different Caesar shift...
#
# Historical context:
#   Invented by Giovan Battista Bellaso in 1553, but misattributed to
#   Blaise de Vigenère in the 19th century...
#
# Security: Broken - vulnerable to Kasiski examination and frequency analysis
#
# Related: beaufort, variant, autokey, caesar
#
# Learn more:
#   • https://en.wikipedia.org/wiki/Vigenère_cipher
#   • http://practicalcryptography.com/ciphers/vigenere-gronsfeld-and-autokey-cipher/
```

### Cipher Metadata
**Status**: Partially Completed

- ✅ Security classification (broken/weak/educational) - included in glossary
- ✅ Historical usage period - included in glossary entries
- 🔜 Difficulty ratings (beginner/intermediate/advanced)
- 🔜 Common use cases (CTF, historical documents, etc.)

---

## Phase 2: Advanced Analysis Features

### Cryptanalysis Tools
- Frequency analysis for ciphertext
- Index of Coincidence calculator
- Kasiski examination for Vigenere
- Pattern detection and statistics
- Auto-detection of likely cipher type

### Chain Analysis
- Visual representation of decode chains
- Confidence scoring for each step
- Export decode paths for documentation

### Example Usage:
```bash
svelo --analyze "encoded_text.txt"
# Shows frequency analysis, likely cipher types, IC score, etc.
```

---

## Phase 3: Interactive Learning Mode

### Tutorial System
- Step-by-step cipher tutorials
- Practice exercises with solutions
- "Crack this cipher" challenges
- Guided walkthroughs for beginners

### Visual Representations
- ASCII art grid for Playfair square
- Rail fence visualization
- Columnar transposition grids
- Caesar wheel representation

### Example:
```bash
svelo --tutorial playfair
# Interactive tutorial explaining and demonstrating Playfair cipher
```

---

## Phase 4: Extended Cipher Support

### Additional Classical Ciphers
- Four-square cipher
- Two-square cipher
- Bifid cipher
- Trifid cipher
- Nihilist cipher
- Homophonic substitution
- Book cipher
- Grille cipher (Cardan grille)

### Modern Encodings
- Punycode
- Quoted-printable
- UUencode
- BinHex
- yEnc

### Format-Specific Decoders
- PEM/DER certificate parsing
- QR code data extraction (if stdlib supports)
- Barcode formats
- HTML/XML entity decoding

---

## Phase 5: Educational Resources

### Reference Library
- Cipher comparison charts
- Historical timeline of cryptography
- Famous historical cipher messages
- Cryptanalysis techniques guide

### Learning Paths
- Beginner's guide to cryptography
- CTF cryptography challenges guide
- Historical cipher restoration guide

### Export Features
- Save analysis reports
- Export educational summaries
- Generate practice problems

---

## Phase 6: Community & Collaboration

### GitHub Features
- "Good first issue" labels for beginners
- Cipher request tracking
- Educational content contributions
- Translation support (i18n)

### Documentation
- Video tutorials (linked from CLI)
- Blog posts on historical ciphers
- Cryptanalysis technique guides
- Contribution showcase

---

## Long-term Vision

### Possible Future Directions
- Web interface (separate project)
- Plugin system for custom ciphers
- Cipher design tool (create your own cipher)
- Competitive learning (timed challenges)
- Integration with CTF platforms

### Research & Historical
- Rare cipher implementations
- Historical document decoder assistance
- Academic research tool features

---

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to help with any of these roadmap items.

**Current Priorities:**
1. ~~Glossary system implementation~~ ✅ Completed
2. Cipher metadata and descriptions (in progress - security levels added)
3. Additional classical cipher support
4. Cryptanalysis tools (frequency analysis, IC calculator)
5. Tutorial/learning mode

**Help Wanted:**
- Historical research on ciphers
- Educational content writing
- Test case development
- Documentation improvements

---

## Status Legend
- **Planned**: Concept defined, not started
- **In Progress**: Actively being developed
- **Completed**: Implemented and merged
- **On Hold**: Waiting for dependencies or decisions

---

Last Updated: 2025-12-30

*This roadmap is a living document. Priorities may shift based on community feedback and contributions.*
