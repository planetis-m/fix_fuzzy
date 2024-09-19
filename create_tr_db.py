import os
import sqlite3
import polib

# ----------------------------- Configuration ----------------------------- #

# Define the root directory containing the 'messages' folder
base_dir = "messages"  # Replace with your actual path

# Define the path for the SQLite database
database_path = "kde_l10n_el.db"  # Replace with desired DB path

# Batch size for inserting records
batch_size = 1000

# ----------------------------- Functions ----------------------------- #

def create_database(conn):
  """
  Creates the translations table in the SQLite database with simplified fields.
  """
  cursor = conn.cursor()
  cursor.execute('''
  CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT,
    filename TEXT,
    msgid TEXT,
    msgstr TEXT,
    msgid_plural TEXT,
    msgstr_plural TEXT,
    msgctxt TEXT,
    occurrences TEXT,
    previous_msgctxt TEXT,
    previous_msgid TEXT,
    previous_msgid_plural TEXT,
    linenum INTEGER,
    fuzzy BOOLEAN,
    obsolete BOOLEAN
  )
  ''')
  conn.commit()

def create_indexes(conn):
  """
  Creates indexes on key columns to optimize query performance.
  """
  cursor = conn.cursor()
  cursor.execute("CREATE INDEX IF NOT EXISTS idx_project ON translations(project)")
  cursor.execute("CREATE INDEX IF NOT EXISTS idx_filename ON translations(filename)")
  cursor.execute("CREATE INDEX IF NOT EXISTS idx_fuzzy ON translations(fuzzy)")
  cursor.execute("CREATE INDEX IF NOT EXISTS idx_obsolete ON translations(obsolete)")
  conn.commit()

def parse_po_files(base_dir, conn):
  """
  Walk through the root directory, parse .po files, and insert entries into the database.
  """
  cursor = conn.cursor()
  # Prepare the insertion statement
  insert_query = '''
  INSERT INTO translations (
    project, filename, msgid, msgstr, msgid_plural, msgstr_plural,
    msgctxt, occurrences, previous_msgctxt, previous_msgid,
    previous_msgid_plural, linenum, fuzzy, obsolete
  )
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  '''
  entries = []
  total_inserted = 0

  for root, _, files in os.walk(base_dir):
    for file in files:
      if file.endswith('.po'):
        file_path = os.path.join(root, file)
        project = os.path.basename(root)
        try:
          po = polib.pofile(file_path)
        except Exception as e:
          print(f"Error parsing {file_path}: {e}")
          continue
        for entry in po:
          # Handle msgstr_plural and msgstr
          msgstr = entry.msgstr
          if entry.msgstr_plural:
            msgstr = entry.msgstr_plural[0]
          msgstr_plural = None
          if entry.msgstr_plural and 1 in entry.msgstr_plural:
            msgstr_plural = entry.msgstr_plural[1]
          # Serialize occurrences as comma-separated string
          occurrences = ','.join(f"{source_file}:{linenum}" for source_file, linenum in entry.occurrences)
          # Determine if 'fuzzy' flag is present
          is_fuzzy = 'fuzzy' in entry.flags
          # Prepare the entry tuple
          entry = (
            project,
            file,
            entry.msgid,
            msgstr,
            entry.msgid_plural,
            msgstr_plural,
            entry.msgctxt,
            occurrences,
            entry.previous_msgctxt,
            entry.previous_msgid,
            entry.previous_msgid_plural,
            entry.linenum,
            is_fuzzy,
            entry.obsolete
          )
          entries.append(entry)
          # Insert in batches
          if len(entries) >= batch_size:
            cursor.executemany(insert_query, entries)
            conn.commit()
            total_inserted += len(entries)
            entries = []
  # Insert any remaining entries
  if entries:
    cursor.executemany(insert_query, entries)
    conn.commit()
    total_inserted += len(entries)
  print(f"Inserted a total of {total_inserted} entries.")

# ----------------------------- Main Function ----------------------------- #

def main():
  # Connect to the SQLite database
  conn = sqlite3.connect(database_path)
  try:
    print("Setting up the database...")
    create_database(conn)
    print("Parsing and inserting data...")
    parse_po_files(base_dir, conn)
    print("Creating indexes...")
    create_indexes(conn)
    print("Database population complete.")
  finally:
    conn.close()

if __name__ == "__main__":
  main()
