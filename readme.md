## Translation Assistance Tools
### Fuzzy Message Repair Tool

This Python script helps improve the quality of translated content
by addressing messages marked as "fuzzy" in translation files.
It offers several automated fixes:

1. Intelligent ampersand insertion:

   Adds ampersand characters for keyboard shortcuts, using the target
   language's letter frequencies as a guide.

2. Case adjustment:

   Modifies capitalization to match the source text more closely.

3. Punctuation refinement:

   Performs simple substitutions, such as replacing "..." with "…"
   for improved typography.

By automating these common adjustments, this tool streamlines the
translation review process and enhances overall text consistency.

<img src="screenshots/image_1.png" alt="Screenshot of Repair Tool" width="50%" />

### Fuzzy Editor Tool

A new editor tool has been added that allows for interactive processing
of the .po files.

## Installation

<img src="screenshots/image_2.png" alt="Screenshot of Editor" width="50%" />

### Prerequisites

- Python 3.x
- pip (Python's package installer)

### Steps

1. **Clone the repository:**

   ```sh
   git clone https://github.com/planetis/fix_fuzzy.git
   cd fix_fuzzy
   ```

2. **Create and activate a virtual environment:**

   ```sh
   python -m venv venv
   ```

   - On Windows:
     ```sh
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```sh
     source venv/bin/activate
     ```

3. **Install the dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

## Usage

```sh
# Repair Tool
python fuzzy_repair_tool.py /path/to/directory
# ...works automatically saving the results.

# Editor
# Filters which fuzzy entries to edit based on the available options:
# --filter-type whitespace_punctuation | character_difference
# --no-filter
# --max-char-diff N (default 2)
python fyzzy_editor.py /path/to/directory
# You will be greeted with a view of the currently selected
# fuzzy entry and the following options: [E]dit, [W]rite, or [S]kip
#
# Notes:
# Pressing Ctrl+E during editing will open the system $EDITOR
# Ctrl+C will exit the program, saving current progress.
```
