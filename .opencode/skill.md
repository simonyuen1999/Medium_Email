# Medium Email Project Skill

## Project Purpose
Centralize Medium articles/emails for offline reading and browsing.

## Key Scripts

| Script | Purpose |
|--------|---------|
| `Read_Medium_From_Gmail.py` | Fetch Medium emails from Gmail, extract article JSON |
| `Merge_Medium_Articles.py` | Merge article files into master store |
| `Article_Classifier.py` | Classify/tag articles |
| `Medium_Article_Browser.py` | Tkinter UI to browse stored articles |
| `Web_Article_Browser.py` | Browser for web articles |
| `Enhanced_Articles_Tk.py` | Enhanced Tkinter article browser |

## Running Agents

### Setup
```bash
# Activate virtual environment
source ls/bin/activate

# Load Gmail env vars (if needed)
source set_gmail_env.sh
```

### Common Tasks

- **Extract new articles**: `python Read_Medium_From_Gmail.py`
- **Merge articles**: `python Merge_Medium_Articles.py`
- **Classify articles**: `python Article_Classifier.py`
- **Browse articles**: `python Medium_Article_Browser.py`

## Data Locations
- Article JSON files: Check project root or `data/` directory
- Master store: `master_articles.json` or similar

## Dependencies
- See `pyproject.toml`
- Install: `python -m pip install -e .`

## File Format Libraries
| Format | Library | Use Case |
|--------|---------|----------|
| PDF | PyPDF2 | Read/write PDF files |
| PPTX | python-pptx | PowerPoint files |
| Excel | openpyxl | Excel .xlsx files |
| Word/DOCX | python-docx | Word documents |
| CSV | csv (built-in) | CSV files |
| JSON | json (built-in) | JSON files |

## Email Clients
| Client | Library | Use Case |
|--------|---------|----------|
| Outlook | pywin32 (win32com.client) | Windows Outlook automation |
| Gmail | google-api-python-client | Gmail API access |
