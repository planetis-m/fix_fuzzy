import os
import polib
from termcolor import colored
from difflib import SequenceMatcher
from prompt_toolkit import prompt
import string
import select
import sys
import time
import argparse

def highlight_spaces(text):
  translation_table = str.maketrans({
    ' ': '·',
    '\n': '↵\n'
  })
  return text.translate(translation_table)

def colored_inline_diff(str1, str2):
  # Create a SequenceMatcher object
  matcher = SequenceMatcher(None, str1, str2)
  # Process the diff
  for op, i1, i2, j1, j2 in matcher.get_opcodes():
    if op == 'equal':
      print(str1[i1:i2], end='')
    elif op == 'delete':
      print(colored(highlight_spaces(str1[i1:i2]), 'white', 'on_red'), end='')
    elif op == 'insert':
      print(colored(highlight_spaces(str2[j1:j2]), 'green'), end='')
    elif op == 'replace':
      print(colored(highlight_spaces(str1[i1:i2]), 'white', 'on_red') + \
          colored(highlight_spaces(str2[j1:j2]), 'green'), end='')
  print()  # Add a newline at the end

def print_old_message(str1, str2):
  matcher = SequenceMatcher(None, str1, str2)
  for op, i1, i2, j1, j2 in matcher.get_opcodes():
    if op == 'equal':
      print(str1[i1:i2], end='')
    elif op in ['delete', 'replace']:
      highlighted = highlight_spaces(str1[i1:i2])
      print(colored(highlighted, 'white', 'on_red'), end='')
  print()  # Add a newline at the end

def print_new_message(str1, str2):
  matcher = SequenceMatcher(None, str1, str2)
  for op, i1, i2, j1, j2 in matcher.get_opcodes():
    if op == 'equal':
      print(str2[j1:j2], end='')
    elif op in ['insert', 'replace']:
      highlighted = highlight_spaces(str2[j1:j2])
      print(colored(highlighted, 'green'), end='')
  print()  # Add a newline at the end

def print_header(text, **kwargs):
  print(colored(f"\n=== {text} ===\n", "yellow", attrs=["bold"]), **kwargs)

def print_subheader(text, **kwargs):
  print(colored(f"\n ─ {text}", "cyan"), **kwargs)

def print_info(text, **kwargs):
  print(colored(f"{text}", "magenta", attrs=["bold"]), **kwargs)

def print_change(text, **kwargs):
  print(colored(f"  ↳ {text}", "green"), **kwargs)

def print_unchanged(text, **kwargs):
  print(colored(f"  ↳ {text}", "dark_grey"), **kwargs)

def print_context(text,  **kwargs):
  print(colored(f"{text}", "white", attrs=["dark"]))

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
  print(colored(line, "light_grey"))

def prefill_input(prompt_text, default_text):
  """Get user input with a prefilled default text. Multiline input supported."""
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

  if entry.msgctxt:
    print_context(f" ─ {entry.msgctxt}")
    if entry.previous_msgctxt:
      if entry.msgctxt != entry.previous_msgctxt:
        print_context(f"  ↳ (previous: {entry.previous_msgctxt})")
      else:
        print_context("  ↳ (matches previous)")

  if old_msgid:
    print_subheader("Previous message")
    print_old_message(old_msgid, new_msgid)
    if old_msgid_plural:
      if new_msgid_plural:
        print_old_message(old_msgid_plural, new_msgid_plural)
      else:
        print(old_msgid_plural)
  print_subheader("New message")
  if old_msgid:
    print_new_message(old_msgid, new_msgid)
  else:
    print(new_msgid)
  if new_msgid_plural:
    if old_msgid_plural:
      print_new_message(old_msgid_plural, new_msgid_plural)
    else:
      print(new_msgid_plural)
  # Show the current msgstr
  print_subheader("Translation")
  current_msgstr = entry.msgstr_plural[0] if entry.msgstr_plural else entry.msgstr
  print(current_msgstr)
  is_msgstr_plural = bool(entry.msgstr_plural) and 1 in entry.msgstr_plural
  if is_msgstr_plural:
    print(entry.msgstr_plural[1])

  # Prompt the user for action (edit, write, or skip)
  try:
    while True:
      action = input("\nChoose an action - [E]dit, [W]rite, or [S]kip: ").strip().lower()
      if action in ['e', 'ε']:
        new_msgstr = prefill_input("msgstr[0]" if is_msgstr_plural else "msgstr", current_msgstr)
        new_msgstr_plural = None
        if is_msgstr_plural:
          new_msgstr_plural = prefill_input("msgstr[1]", entry.msgstr_plural[1])
        # Update the msgstr if it was edited
        if current_msgstr != new_msgstr or \
            (is_msgstr_plural and entry.msgstr_plural[1] != new_msgstr_plural):
          print_change(f"Entry updated:")
          colored_inline_diff(current_msgstr, new_msgstr)
          if is_msgstr_plural:
            colored_inline_diff(entry.msgstr_plural[1], new_msgstr_plural)
        else:
          print_change("No changes made.")
        sec_to_skip = 2
        pause_action = \
          input_with_timeout(f"\nSaving in {sec_to_skip}s... (Press ENTER to interrupt)", sec_to_skip)
        if not pause_action:
          if is_msgstr_plural:
            entry.msgstr_plural[0] = new_msgstr
            entry.msgstr_plural[1] = new_msgstr_plural
          else:
            entry.msgstr = new_msgstr
          return True
      elif action in ['w', 'ς']:
        # Just save the current msgstr
        return True
      elif action in ['s', 'σ']:
        # Skip saving changes
        restore_original(entry)
        return False
  except BaseException:
    print_info("\nEditing interrupted. Exiting...")
    restore_original(entry)
    raise
  return False # cannot happen

def process_po_file(filepath, comparison_type, max_char_diff, no_comparison):
  """Process the .po file and handle fuzzy entries."""
  po = polib.pofile(filepath, encoding='utf-8', wrapwidth=80)
  count = 0
  should_quit = False  # Flag to indicate if we should break out of the loop

  try:
    for entry in po.fuzzy_entries():
      if no_comparison or should_edit_entry(entry, comparison_type, max_char_diff):
        if edit_msgstr(entry, filepath):
          count += 1
          entry.flags.remove('fuzzy')  # Remove the fuzzy flag
  except (KeyboardInterrupt, SystemExit):
    should_quit = True
  if count > 0:
    print_info(f"Saving changes to {filepath}...")
    po.save()
  return count, should_quit

def scan_directory(directory, comparison_type, max_char_diff, no_comparison):
  """Scan the directory for .po files and process them."""
  total_count = 0
  for root, _, files in os.walk(directory):
    should_quit = False
    for file in files:
      if file.endswith('.po'):
        filepath = os.path.join(root, file)
        count, should_quit = process_po_file(filepath, comparison_type, max_char_diff, no_comparison)
        total_count += count
        if should_quit:
          break
    if should_quit:
      break
  print_info(f"Changes made: {total_count}")

def should_edit_entry(entry, comparison_type, max_char_diff):
  """Determine whether an entry should be edited based on comparison type."""
  previous_msgid = entry.previous_msgid
  msgid = entry.msgid

  if previous_msgid is None or msgid is None:
    return False

  if comparison_type == 'whitespace_punctuation':
    return strings_differ_by_whitespace_and_punctuation(previous_msgid, msgid)
  elif comparison_type == 'character_difference':
    return strings_differ_by_n_chars(previous_msgid, msgid, max_char_diff)
  return False

def strings_differ_by_whitespace_and_punctuation(str1, str2):
  """Check if two strings differ only by whitespace and punctuation."""
  normalized_str1 = normalize_string(str1)
  normalized_str2 = normalize_string(str2)

  return normalized_str1 == normalized_str2

def normalize_string(s):
  """Normalize a string by lowercasing, removing punctuation, and normalizing whitespace."""
  normalized = []
  prev_char = None
  punctuation = string.punctuation + "…"
  for ch in s:
    if ch in punctuation:
      continue  # Skip punctuation
    if ch.isspace():
      # Only append a single space when encountering multiple spaces
      if prev_char != ' ':
        normalized.append(' ')
      prev_char = ' '
    else:
      normalized.append(ch.lower())
      prev_char = ch.lower()
  return ''.join(normalized).strip()

def strings_differ_by_n_chars(str1, str2, max_char_diff):
  """Check if two strings differ by no more than N characters."""
  # Use SequenceMatcher to compute the similarity ratio
  matcher = SequenceMatcher(None, str1, str2)
  # Get the number of character differences
  diff_chars = int((1 - matcher.ratio()) * max(len(str1), len(str2)))
  return diff_chars <= max_char_diff

def parse_args():
  parser = argparse.ArgumentParser(description="An interactive editor for fuzzy translation entries in .po files.")
  parser.add_argument('directory', help="The directory to scan for .po files.")
  parser.add_argument('--filter-type', choices=['whitespace_punctuation', 'character_difference'],
                      default='whitespace_punctuation', help="The type of comparison to use.")
  parser.add_argument('--max-char-diff', type=int, default=2,
                      help="The maximum number of character differences allowed (used only with 'character_difference').")
  parser.add_argument('--no-filter', action='store_true', help="Disable comparison checks and edit all fuzzy entries.")
  return parser.parse_args()

if __name__ == "__main__":
  args = parse_args()
  scan_directory(args.directory, args.filter_type, args.max_char_diff, args.no_filter)
