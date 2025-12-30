# Contributing to Svelo

Thank you for your interest in contributing to Svelo! This project aims to be a comprehensive educational tool for learning about classical and modern cryptography.

## Vision

Svelo is growing from a simple decoder CLI into a robust educational resource for cryptography enthusiasts, CTF players, and students. We welcome contributions that help achieve this mission.

## How to Contribute

### Types of Contributions We're Looking For

- **New ciphers and encodings**: Add support for additional classical or modern ciphers
- **Educational content**: Documentation, explanations, and learning resources
- **Glossary entries**: Add explanations and reference links for cryptographic concepts
- **Interactive features**: Improve the user experience and interactive menu
- **Test coverage**: Add tests for existing or new functionality
- **Bug fixes**: Fix issues or improve accuracy of existing decoders
- **Performance improvements**: Optimize decoding algorithms
- **Examples and tutorials**: Real-world use cases and learning guides

### Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Svelo.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest`
6. Commit your changes: `git commit -m "Add: description of your changes"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

### Development Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -e ".[dev]"
pytest
```

### Code Guidelines

- **Keep it stdlib-only**: This project avoids external dependencies to maintain simplicity and security
- **Add tests**: All new decoders/encoders should include tests in `tests/`
- **Document your code**: Add docstrings for complex functions
- **Follow existing patterns**: Match the style of existing code
- **Update README**: Add your cipher/feature to the documentation

### Adding a New Cipher

1. Add decoding logic to `src/svelo/decoders.py`
2. Add encoding logic (if applicable) to the same file
3. Register in `get_decoders()` or `get_encoders()`
4. Add to the appropriate list in `src/svelo/cli.py`
5. Add tests to `tests/test_decoders.py`
6. Update README.md with the new cipher name

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_decoders.py

# Run with coverage
pytest --cov=svelo
```

## Roadmap Ideas

See [ROADMAP.md](ROADMAP.md) for our development roadmap. Some areas we're particularly interested in:

- **Glossary system**: In-app explanations of cryptographic concepts
- **Historical context**: Background on when/where ciphers were used
- **Reference links**: Connections to learning resources
- **Visual modes**: ASCII art representations of cipher mechanics
- **Cipher comparison**: Side-by-side comparison of related ciphers
- **Difficulty ratings**: Educational difficulty levels for each cipher

## Questions or Ideas?

- Open an issue to discuss new features
- Check existing issues for "good first issue" or "help wanted" labels
- Start a discussion about educational content improvements

## Code of Conduct

Be respectful, inclusive, and constructive. We're here to learn and teach cryptography, not to gatekeep knowledge.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
