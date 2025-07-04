# Installation Guide

## Prerequisites

### 1. Python Installation
- Python 3.8 or higher required
- Check with: `python --version`

### 2. Tesseract OCR Installation

#### Windows
1. Download from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install the executable
3. Add to PATH or note installation directory
4. Verify: `tesseract --version`

#### macOS
```bash
brew install tesseract
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### 3. Poppler Utils Installation

#### Windows
1. Download from [Poppler for Windows](http://blog.alivate.com.au/poppler-windows/)
2. Extract and add to PATH
3. Verify: `pdftoppm -h`

#### macOS
```bash
brew install poppler
```

#### Ubuntu/Debian
```bash
sudo apt-get install poppler-utils
```

## Application Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd tesarac
```

### 2. Virtual Environment (Recommended)
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Application
```bash
python start.py
```

### 5. Access Dashboard
Open browser to: http://localhost:5000

## Verification

### System Check
The application performs automatic system checks on startup:
- Python environment
- Required packages
- Tesseract availability
- Poppler utilities

### Test Upload
1. Upload a sample PDF
2. Check processing status
3. Download extracted text
4. Review logs in `api.log`

## Troubleshooting

### Common Issues

**Tesseract not found**
- Ensure proper installation
- Check PATH variable
- Try full path configuration

**Poppler utilities missing**
- Install poppler-utils package
- Verify pdftoppm command works

**Port already in use**
- Change port in app.py
- Kill existing process: `lsof -ti:5000 | xargs kill`

**Permission errors**
- Check file permissions
- Run with appropriate user privileges
- Verify directory write access
