"""
    support functions for theatrical_fundraiser_webapp.py
"""

import os.path, sqlite3, random, json
database = 'donors.db'

def populate_characters():
    conn = sqlite3.connect(database)
    crsr = conn.cursor()
    with open('static/assets/data/select_unique_chars.json', 'r') as jsonfile:
        plays = json.load(jsonfile)
    for play in plays:
        for char in plays[play]:
            crsr.execute("INSERT INTO characters VALUES (?,?,?);", (char, play, None))
    conn.commit()
    crsr.close()
    conn.close()

def create_tables():
    conn = sqlite3.connect(database)
    crsr = conn.cursor()
    crsr.execute("""
        CREATE TABLE donors(
            firstname TEXT,
            lastname TEXT,
            street TEXT,
            city TEXT,
            state TEXT,
            zip INT,
            email TEXT UNIQUE,
            donor_id INT NOT NULL UNIQUE
        )
    """)
    crsr.execute("""
        CREATE TABLE characters(
            character TEXT,
            play TEXT,
            donor_id INT UNIQUE
        )
    """)
    crsr.execute("""
        CREATE TABLE pledges(
            donor_id INT UNIQUE,
            pledge INT
        )
    """)
    conn.commit()
    crsr.close()
    conn.close()

def next_ID_number():
    conn = sqlite3.connect(database)
    crsr = conn.cursor()
    pids = [ t[0] for t in crsr.execute("SELECT donor_id FROM donors;").fetchall() ]
    crsr.close()
    conn.close()
    if not pids:
        return 101
    else:
        return max(pids) + 1

def int_to_dollar_string(amount):
    outstring = str(amount)
    i = 3
    while (len(outstring) > i):
        outstring = outstring[:-i] + ',' + outstring[-i:]
        i += 4
    outstring = '$' + outstring
    return outstring

def generate_palette():
    palette = []
    values = [ "00", "7F", "FF" ]
    for r in values:
        for g in values:
            for b in values:
                if ( r == g and g == b ) or ( int(r,base=16) + int(g,base=16) + int(b,base=16) > 510 ):
                    continue
                else:
                    palette.append(f"#{r}{g}{b}")
    random.shuffle(palette)
    return palette
