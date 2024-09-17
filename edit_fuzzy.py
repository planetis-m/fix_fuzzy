import os
import polib
import tempfile
import subprocess
from termcolor import colored
from difflib import SequenceMatcher
from prompt_toolkit import prompt
import select
import sys
import time

def open_editor_with_content(initial_content):
  """Open the user's default editor to edit multiline text."""
  # Create a temporary file
  with tempfile.NamedTemporaryFile(suffix=".tmp", mode='w+', delete=False) as tmp_file:
    # Write initial content (the current msgstr) to the temporary file
    tmp_file.write(initial_content)
    tmp_file_name = tmp_file.name
  # Try to get the user's default editor from environment variables, fallback to 'nano'
  editor = os.environ.get('EDITOR', 'nano')
  # Open the temporary file in the editor
  subprocess.call([editor, tmp_file_name])
  # After the user closes the editor, read the file back
  with open(tmp_file_name, 'r') as tmp_file:
    edited_content = tmp_file.read()
  # Clean up the temporary file
  os.remove(tmp_file_name)

  return edited_content.rstrip('\n')

def colored_inline_diff(str1, str2):
  # Create a SequenceMatcher object
  matcher = SequenceMatcher(None, str1, str2)
  # Process the diff
  for op, i1, i2, j1, j2 in matcher.get_opcodes():
    if op == 'equal':
      print(str1[i1:i2], end='')
    elif op == 'delete':
      print(colored(str1[i1:i2], 'white', 'on_red'), end='')
    elif op == 'insert':
      print(colored(str2[j1:j2], 'green'), end='')
    elif op == 'replace':
      print(colored(str1[i1:i2], 'white', 'on_red') + colored(str2[j1:j2], 'green'), end='')
  print()  # Add a newline at the end

def print_header(text, **kwargs):
  print(colored(f"\n=== {text} ===\n", "yellow", attrs=["bold"]), **kwargs)

def print_subheader(text, **kwargs):
  print(colored(f" ─ {text}", "cyan"), **kwargs)

def print_info(text, **kwargs):
  print(colored(f"{text}", "magenta", attrs=["bold"]), **kwargs)

def print_change(text, **kwargs):
  print(colored(f"  ↳ {text}", "green"), **kwargs)

def print_unchanged(text, **kwargs):
  print(colored(f"  ↳ {text}", "dark_grey"), **kwargs)

def input_with_timeout(prompt, timeout=10):
  print_info(prompt, end='', flush=True)
  rlist, _, _ = select.select([sys.stdin], [], [], timeout)
  if rlist:
    return sys.stdin.readline()
  else:
    print_info("\nTimeout reached. Continuing...")
    return None

def line_print(width=80):
  line = "─" * width
  print(colored(line, "light_grey", attrs=['dark']))

def prefill_input(prompt_text, default_text):
  """
  Get user input with a prefilled default text. Multiline input supported.

  Keybindings:
    - Esc and then Enter to accept input.
    - Ctrl-E to open the input in an external editor.
  """
  line_print()
  result = prompt(f"{prompt_text}:\n", default=default_text, multiline=True,
                  enable_open_in_editor=True, tempfile_suffix=".txt")
  line_print()
  return result

def edit_msgstr(entry, filepath):
  """Function to edit msgstr with multiline editing support and pre-applied changes."""
  print_header(f"Editing fuzzy entry in {filepath}:{entry.linenum}")

  old_msgid = entry.previous_msgid
  new_msgid = entry.msgid
  old_msgid_plural = entry.previous_msgid_plural
  new_msgid_plural = entry.msgid_plural

  # Store the original msgstr and msgstr_plural to restore if user skips
  original_msgstr = entry.msgstr
  original_msgstr_plural = None
  if entry.msgstr_plural:
    original_msgstr_plural = entry.msgstr_plural.copy()

  def restore_original(entry):
    entry.msgstr = original_msgstr
    if original_msgstr_plural:
      entry.msgstr_plural = original_msgstr_plural

  if old_msgid:
    print_subheader("Previous message:")
    print(old_msgid)
    if old_msgid_plural:
      print(old_msgid_plural)
  print_subheader("New message:")
  print(new_msgid)
  if new_msgid_plural:
    print(new_msgid_plural)
  # Show the current msgstr
  print_subheader("Translation:")
  current_msgstr = entry.msgstr_plural[0] if entry.msgstr_plural else entry.msgstr
  print(current_msgstr)
  is_msgstr_plural = bool(entry.msgstr_plural) and 1 in entry.msgstr_plural
  if is_msgstr_plural:
    print(entry.msgstr_plural[1])

  # Prompt the user for action (edit, write, or skip)
  while True:
    action = input("\nChoose an action - [E]dit, [W]rite, or [S]kip: ").strip().lower()
    if action == 'e':
      new_msgstr = prefill_input("msgstr[0]" if is_msgstr_plural else "msgstr", current_msgstr)
      new_msgstr_plural = None
      if is_msgstr_plural:
        new_msgstr_plural = prefill_input("msgstr[1]", entry.msgstr_plural[1])
      # Update the msgstr if it was edited
      if current_msgstr != new_msgstr or \
          (is_msgstr_plural and entry.msgstr_plural[1] != new_msgstr_plural):
        print_change(f"Entry updated manually:")
        colored_inline_diff(current_msgstr, new_msgstr)
        if is_msgstr_plural:
          colored_inline_diff(entry.msgstr_plural[1], new_msgstr_plural)
      else:
        print_change("No changes made.")
      sec_to_skip = 3
      pause_action = input_with_timeout(f"\nSaving in {sec_to_skip}s...", sec_to_skip)
      if not pause_action:
        if is_msgstr_plural:
          entry.msgstr_plural[0] = new_msgstr
          entry.msgstr_plural[1] = new_msgstr_plural
        else:
          entry.msgstr = new_msgstr
        return True
    elif action == 'w':
      # Just save the current msgstr (possibly pre-applied changes)
      return True
    elif action == 's':
      # Skip saving changes
      restore_original(entry)
      return False
  return False # cannot happen

def process_po_file(filepath):
  """Process the .po file and handle fuzzy entries."""
  po = polib.pofile(filepath, encoding='utf-8', wrapwidth=80)
  count = 0
  for entry in po.fuzzy_entries():
    if edit_msgstr(entry, filepath):
      count += 1
      entry.flags.remove('fuzzy')  # Remove the fuzzy flag
  if count > 0:
    print_info(f"Saving changes to {filepath}...")
    po.save()
  return count

def scan_directory(directory):
  """Scan the directory for .po files and process them."""
  count = 0
  for root, _, files in os.walk(directory):
    for file in files:
      if file.endswith('.po'):
        filepath = os.path.join(root, file)
        count += process_po_file(filepath)
  print_info(f"Changes made: {count}")

if __name__ == "__main__":
  directory = input("Enter the directory to scan for .po files: ").strip()
  scan_directory(directory)
