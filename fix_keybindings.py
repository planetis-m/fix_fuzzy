import random
import os
import string
import polib
from termcolor import colored
from difflib import SequenceMatcher

# Warning: BUG
# msgid "&Quit <application>%1</application>"
# -msgstr "&Έξοδος <application>%1</application>"
# +msgstr "Έξοδος <applicatio&n>%1</application>"

# Letter Frequencies of the Greek language
GREEK_LETTER_PENALTIES = {
  'α': 10.81, 'τ': 7.99, 'ο': 7.23, 'ε': 7.18, 'σ': 7.00, 'ι': 6.64,
  'ν': 6.19, 'ρ': 4.32, 'π': 4.15, 'κ': 3.77, 'μ': 3.43, 'η': 3.18,
  'υ': 3.04, 'λ': 2.66, 'γ': 1.70, 'δ': 1.63, 'χ': 1.29, 'ω': 1.23,
  'θ': 1.22, 'φ': 0.74, 'β': 0.67, 'ξ': 0.44, 'ζ': 0.33, 'ψ': 0.15
}

# List of Greek letters to exclude
EXCLUDED_LETTERS = {'ά', 'έ', 'ή', 'ί', 'ό', 'ύ', 'ώ', 'ϊ', 'ϋ', 'ΐ', 'ΰ', 'ς'}

def detect_invalid_ampersand_usage(msgstr):
  """Detect non-escaped ampersands (&) that precede certain Greek characters."""
  # Remove escaped ampersands (&&)
  cleaned_str = msgstr.replace('&&', '')
  for i in range(len(cleaned_str) - 1):
    if cleaned_str[i] == '&' and cleaned_str[i + 1].lower() in EXCLUDED_LETTERS:
      return True
  return False

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

def edit_msgstr(entry, filepath):
  old_msgstr = entry.msgstr

  if old_msgstr and detect_invalid_ampersand_usage(old_msgstr) and \
      not entry.msgstr_plural:
    print_header(f"Editing entry in {filepath}:{entry.linenum}")
    print_subheader(f"Detected invalid ampersand usage in msgstr:")
    print(entry.msgid)

    ampersands_count = old_msgstr.count('&') - old_msgstr.count('&&') * 2
    new_msgstr = remove_unescaped_ampersand(old_msgstr, ampersands_count)
    new_msgstr = assign_ampersand_randomly(new_msgstr, ampersands_count)

    print_change("Entry updated automatically:")
    colored_inline_diff(old_msgstr, new_msgstr)

    entry.msgstr = new_msgstr
    return True
  else:
    return False

def process_po_file(filepath):
  """Process the .po file and handle fuzzy entries."""
  po = polib.pofile(filepath, encoding='utf-8', wrapwidth=80)
  count = 0
  for entry in po.translated_entries():
    if edit_msgstr(entry, filepath):
      count += 1
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
