# Contributing to Medical PDF OCR Dashboard

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature/fix
4. Make your changes
5. Test thoroughly
6. Submit a pull request

## Development Setup

```bash
git clone https://github.com/yourusername/tesarac.git
cd tesarac
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small
- Use type hints where appropriate

## Project Structure

```
tesarac/
├── src/                    # Core application modules
├── static/                 # Frontend assets (CSS, JS)
├── templates/              # HTML templates
├── docs/                   # Documentation
├── uploads/                # File upload directory
├── outputs/                # Processed file output
├── app.py                  # Main Flask application
└── start.py               # Application launcher
```

## Testing

Before submitting changes:

1. Test the web interface thoroughly
2. Verify API endpoints work correctly
3. Test with different PDF file types
4. Check error handling scenarios
5. Ensure no existing functionality is broken

## Areas for Contribution

### High Priority
- Enhanced OCR accuracy
- Additional file format support
- Performance optimizations
- Mobile UI improvements
- Comprehensive test suite

### Medium Priority
- User authentication
- File management features
- Advanced analytics
- API rate limiting
- Docker containerization

### Documentation
- API documentation improvements
- User guides and tutorials
- Code documentation
- Deployment guides

## Pull Request Process

1. **Create a descriptive branch name**
   ```bash
   git checkout -b feature/add-user-auth
   git checkout -b fix/upload-error-handling
   ```

2. **Make focused commits**
   - One logical change per commit
   - Write clear commit messages
   - Reference issues when applicable

3. **Update documentation**
   - Update README if needed
   - Add/update API docs for new endpoints
   - Include inline code documentation

4. **Test your changes**
   - Test manually in the web interface
   - Verify API endpoints work
   - Check for regressions

5. **Submit pull request**
   - Use a clear, descriptive title
   - Provide detailed description of changes
   - Reference related issues
   - Include screenshots for UI changes

## Commit Message Format

```
type(scope): brief description

Detailed explanation if necessary

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

### Review Criteria
- Code quality and style
- Functionality and correctness
- Performance implications
- Security considerations
- Documentation completeness

## Reporting Issues

When reporting issues:

1. Use a clear, descriptive title
2. Provide detailed steps to reproduce
3. Include relevant error messages
4. Specify your environment (OS, Python version, etc.)
5. Add screenshots if applicable

## Feature Requests

For new feature requests:

1. Check if it already exists in issues
2. Provide clear use case description
3. Explain the expected behavior
4. Consider implementation complexity
5. Be open to discussion and alternatives

## Security

If you discover security vulnerabilities:

1. Do NOT open a public issue
2. Email the maintainers directly
3. Provide detailed information
4. Allow time for proper fix before disclosure

## Questions?

- Open an issue for general questions
- Join discussions in existing issues
- Check documentation first

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

Thank you for contributing!
