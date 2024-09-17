import random
import os
# import string
import polib
from termcolor import colored
from difflib import SequenceMatcher

# Letter Frequencies of the Greek language
GREEK_LETTER_PENALTIES = {
  'α': 10.81, 'τ': 7.99, 'ο': 7.23, 'ε': 7.18, 'σ': 7.00, 'ι': 6.64,
  'ν': 6.19, 'ρ': 4.32, 'π': 4.15, 'κ': 3.77, 'μ': 3.43, 'η': 3.18,
  'υ': 3.04, 'λ': 2.66, 'γ': 1.70, 'δ': 1.63, 'χ': 1.29, 'ω': 1.23,
  'θ': 1.22, 'φ': 0.74, 'β': 0.67, 'ξ': 0.44, 'ζ': 0.33, 'ψ': 0.15
}

# List of Greek letters to exclude
EXCLUDED_LETTERS = {'ά', 'έ', 'ή', 'ί', 'ό', 'ύ', 'ώ', 'ϊ', 'ϋ', 'ΐ', 'ΰ', 'ς'}

def detect_ampersand_changes(old_msgid, new_msgid):
  """
  Detect if an ampersand (&) has been added or removed between old_msgid and new_msgid.
  Ignore escaped ampersands (&&).
  """
  # Count non-escaped ampersands (&) by removing '&&' and counting remaining '&'
  old_ampersands = old_msgid.count('&') - old_msgid.count('&&') * 2
  new_ampersands = new_msgid.count('&') - new_msgid.count('&&') * 2

  return old_ampersands, new_ampersands

def remove_unescaped_ampersand(msgstr, count_to_remove):
  """
  Remove only unescaped ampersands (&) from the string, leaving escaped ampersands (&&) intact.
  `count_to_remove` specifies how many ampersands to remove.
  """
  result = []
  i = 0
  ampersands_removed = 0
  while i < len(msgstr):
    # Check for escaped ampersands (&&)
    if msgstr[i:i+2] == '&&':
      result.append('&&')
      i += 2  # Skip both '&'
    elif msgstr[i] == '&' and ampersands_removed < count_to_remove:
      # Remove the unescaped ampersand
      ampersands_removed += 1
      i += 1  # Skip this '&'
    else:
      result.append(msgstr[i])
      i += 1
  return ''.join(result)

def apply_ampersand_change(old_msgid, new_msgid, msgstr):
  """
  Apply the ampersand change to msgstr. If ampersand was removed, remove it from msgstr.
  If ampersand was added, assign it randomly to a letter in msgstr.
  """
  old_ampersands, new_ampersands = detect_ampersand_changes(old_msgid, new_msgid)

  if new_ampersands > old_ampersands:
    # Ampersand added, assign it randomly
    ampersands_to_add = new_ampersands - old_ampersands
    return (True, assign_ampersand_randomly(msgstr, ampersands_to_add))
  elif old_ampersands > new_ampersands:
    # Ampersand removed, remove from msgstr
    return (True, remove_unescaped_ampersand(msgstr, old_ampersands - new_ampersands))
  elif new_ampersands > 0:
    # Ampersand's location moved.
    return (True, msgstr)
  return (False, msgstr)

def assign_ampersand_randomly(msgstr, ampersands_to_add):
  """
  Assign ampersands randomly to letters in msgstr.
  Penalize common Greek letters and exclude vowels with diacritics.
  """
  # Filter out excluded vowels and create a list of unique letters in the msgstr
  unique_letters = [ch for ch in set(msgstr.lower()) if ch not in EXCLUDED_LETTERS and ch.isalpha()]

  if not unique_letters:
    # No valid letters to assign ampersands, return unchanged msgstr
    return msgstr

  # Create a list of letters with their penalties
  weighted_letters = []
  for letter in unique_letters:
    penalty = GREEK_LETTER_PENALTIES.get(letter, 1)  # Higher penalty for common letters
    weighted_letters.extend([letter] * int(100 / penalty))  # More penalty = fewer chances

  # Randomly assign ampersands to letters in msgstr
  for _ in range(ampersands_to_add):
    chosen_letter = random.choice(weighted_letters)
    msgstr = insert_ampersand_before_letter(msgstr, chosen_letter)
  return msgstr

def insert_ampersand_before_letter(msgstr, letter):
  """Insert ampersand (&) before the first occurrence of the chosen letter (lowercase or uppercase) in msgstr."""
  lower_letter = letter.lower()
  upper_letter = letter.upper()

  lower_index = msgstr.find(lower_letter)
  upper_index = msgstr.find(upper_letter)

  if lower_index == -1 and upper_index == -1:
    return msgstr # cannot happen
  elif lower_index == -1 or (upper_index != -1 and upper_index < lower_index):
    return msgstr.replace(upper_letter, f'&{upper_letter}', 1)
  else:
    return msgstr.replace(lower_letter, f'&{lower_letter}', 1)

def detect_trailing_changes(old, new):
  """
  Detect if certain trailing characters like '...' have been added or removed
  between the old msgid and new msgid.
  """
  # Define the trailing patterns to look for
  trailing_patterns = ['...', '…', ': ', ':', '.', ', ', ',']

  def find_trailing_pattern(s):
    for pattern in trailing_patterns:
      if s.endswith(pattern):
        return pattern
    return None

  old_trailing = find_trailing_pattern(old)
  new_trailing = find_trailing_pattern(new)

  if old_trailing != new_trailing:
    return old_trailing, new_trailing
  return None, None

def apply_trailing_change(old_msgid, new_msgid, msgstr):
  """
  Automatically apply trailing changes if the trailing pattern has been modified
  between old_msgid and new_msgid.
  """
  old_trailing, new_trailing = detect_trailing_changes(old_msgid, new_msgid)
  if old_trailing is None and new_trailing is None:
    # No trailing changes detected
    return (False, msgstr)
  # Remove old trailing pattern from msgstr if it exists
  if old_trailing and msgstr.endswith(old_trailing):
    msgstr = msgstr[:-len(old_trailing)].rstrip()
  # Add the new trailing pattern to msgstr if a new one exists
  if new_trailing and not msgstr.endswith(new_trailing):
    msgstr = msgstr.rstrip() + new_trailing
  return (True, msgstr)

def apply_case_change(old_msgid, new_msgid, msgstr):
  def sentence_case(s):
    return s[0].upper() + s[1:].lower()
  # Check if new_str is the sentence-cased version of old_msgid
  if sentence_case(old_msgid) == new_msgid:
    # Apply the same sentence casing to msg
    return (True, sentence_case(msgstr))
  if new_msgid[0].islower():
    # Apply lowercase to all letters in msgstr
    return (True, msgstr.lower())
  if old_msgid == sentence_case(new_msgid):
    # Words titled cased, ignore.
    return (True, msgstr)
  return (False, msgstr)

def is_trivial_change(str1, str2):
  """Check if two strings differ only by whitespace and punctuation."""
  normalized_str1 = normalize_string(str1)
  normalized_str2 = normalize_string(str2)

  return normalized_str1 == normalized_str2

def normalize_string(s):
  """Normalize a string by lowercasing, removing punctuation, and normalizing whitespace."""
  normalized = []
  prev_char = None
  # punctuation = string.punctuation + "…"
  punctuation = '.&:,…'
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

def print_header(text):
  print(colored(f"\n=== {text} ===", "yellow", attrs=["bold"]))

def print_subheader(text):
  print(colored(f"  {text}", "cyan"))

def print_info(text):
  print(colored(f"{text}", "magenta", attrs=["bold"]))

def print_change(text):
  print(colored(f"  ↳ {text}", "green"))

def print_unchanged(text):
  print(colored(f"  ↳ {text}", "dark_grey"))

from enum import Enum

class MsgstrChangeStatus(Enum):
  SAVED_AS_IS = 1   # When the entry was saved as is, without further changes
  AUTO_APPLIED = 2  # When the change was auto-applied to msgstr
  UNCHANGED = 3     # When no changes were applied

def process_msgstr_change(current_msgstr, new_msgstr, change_applied):
  """
  Process the changes to msgstr, returning the new msgstr and a status Enum representing the result.
  """
  if new_msgstr != current_msgstr:
    return MsgstrChangeStatus.AUTO_APPLIED  # Change is auto-applied
  elif change_applied:
    return MsgstrChangeStatus.SAVED_AS_IS  # Entry saved as is
  else:
    return MsgstrChangeStatus.UNCHANGED  # No changes applied

def detect_and_preapply_changes(entry, filepath):
  """
  Detect if the msgid or msgid_plural has added or removed trailing characters and apply the same change to msgstr_plural[0] (singular form)
  and msgstr_plural[1] (plural form). If the change is trivial (punctuation, case, etc.), pre-apply it automatically.
  """
  old_msgid = entry.previous_msgid
  new_msgid = entry.msgid
  old_msgid_plural = entry.previous_msgid_plural
  new_msgid_plural = entry.msgid_plural

  # Helper function to apply changes to msgstr (both singular and plural)
  def apply_changes_to_strs(old, new, msgstr):
    change_applied = False
    applied, new_msgstr = apply_ampersand_change(old, new, msgstr)
    change_applied = change_applied or applied
    applied, new_msgstr = apply_trailing_change(old, new, new_msgstr)
    change_applied = change_applied or applied
    applied, new_msgstr = apply_case_change(old, new, new_msgstr)
    change_applied = change_applied or applied
    return change_applied, new_msgstr

  is_trivial_change_plural = bool(old_msgid_plural and new_msgid_plural) and \
      is_trivial_change(old_msgid_plural, new_msgid_plural)
  # Handle singular and plural together if both exist
  if old_msgid and is_trivial_change(old_msgid, new_msgid) and \
      bool(entry.msgstr_plural) == is_trivial_change_plural: # XNOR
    print_header(f"Editing fuzzy entry in {filepath}:{entry.linenum}")
    print_subheader(f"Detected trivial change in msgid:")
    colored_inline_diff(old_msgid, new_msgid)
    if is_trivial_change_plural:
      colored_inline_diff(old_msgid_plural, new_msgid_plural)

    change_applied = False
    # Apply changes to the singular form
    applied, new_msgstr = apply_changes_to_strs(
      old_msgid, new_msgid,
      entry.msgstr_plural[0] if is_trivial_change_plural else entry.msgstr
    )
    change_applied = change_applied or applied

    status = process_msgstr_change(
      entry.msgstr_plural[0] if is_trivial_change_plural else entry.msgstr,
      new_msgstr,
      change_applied or old_msgid == new_msgid
    )
    # If there is a plural form, apply changes to msgstr_plural[1]
    new_msgstr_plural = None
    if entry.msgstr_plural and 1 in entry.msgstr_plural:
      applied, new_msgstr_plural = apply_changes_to_strs(old_msgid_plural,
          new_msgid_plural, entry.msgstr_plural[1])
      change_applied = change_applied or applied

      status_plural = process_msgstr_change(
        entry.msgstr_plural[1],
        new_msgstr_plural,
        change_applied or old_msgid_plural == new_msgid_plural
      )
    else:
      status_plural = MsgstrChangeStatus.SAVED_AS_IS

    if status == MsgstrChangeStatus.UNCHANGED or \
        status_plural == MsgstrChangeStatus.UNCHANGED:
      print_unchanged("Entry NOT changed:")
      print(new_msgstr)
      if is_trivial_change_plural:
        print(new_msgstr_plural)
      return False  # Change is not trivial, skipping

    if status == MsgstrChangeStatus.AUTO_APPLIED:
      print_change("Entry updated automatically:")
      colored_inline_diff(
        entry.msgstr_plural[0] if is_trivial_change_plural else entry.msgstr,
        new_msgstr
      )
      if is_trivial_change_plural:
        colored_inline_diff(entry.msgstr_plural[1], new_msgstr_plural)
    elif status == MsgstrChangeStatus.SAVED_AS_IS:
      print_change("Entry saved as is:")
      print(new_msgstr)
      if is_trivial_change_plural:
        print(new_msgstr_plural)

    if status == MsgstrChangeStatus.AUTO_APPLIED:
      if is_trivial_change_plural:
        entry.msgstr_plural[0] = new_msgstr
        entry.msgstr_plural[1] = new_msgstr_plural
      else:
        entry.msgstr = new_msgstr
    return True
  else:
    # print_unchanged(f"No changes applied due to complexity.")
    return False  # Change is not trivial, skipping

def process_po_file(filepath):
  """Process the .po file and handle fuzzy entries."""
  po = polib.pofile(filepath, encoding='utf-8', wrapwidth=80)
  count = 0
  for entry in po.fuzzy_entries():
    if detect_and_preapply_changes(entry, filepath):
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
