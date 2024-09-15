## Automatically fix fuzzy messages in translations!

This is a Python script that can repair some translation messages that have been marked as fuzzy.
It can add ampersand characters (used for creating keyboard shortcuts) randomly in text using the
target's language letter frequencies as guide. It also can uncapitalize the words and make some
simple substitutions at the end of the message (replacing ... with …, etc)

![image](/uploads/-/system/user/16321/31ba00df7ecb70fcb97e2490094327c9/image.png){width=50% height=50%}

## Installation

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
python autofix_fuzzy/main.py

Enter the directory to scan for .po files: <Path to the 'messages' or a subfolder.>
```
