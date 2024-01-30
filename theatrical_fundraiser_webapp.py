""" Prototype WebApp for Theatrical Fundraisers
    version 0.1
    Henry Eissler & Kathryn Murrell
    1/30/24
"""

from flask import Flask, render_template, request, redirect, url_for
import sqlite3, os.path, json, sys
from tfa_functions import *

app = Flask(__name__)
database = 'donors.db'
chart_palette = []

if not os.path.isfile(database):
    create_tables()
    populate_characters()

# ~~~ HOME ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.route("/")
def home():
    return render_template("home.html", ttitle="Home", tpage="/")

# ~~~ NEW ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.route("/new", methods = ["GET", "POST"])
def create():
    if request.method == "POST":
        formnames = ['givenname', 'surname', 'street', 'city', 'state', 'zip', 'email']
        patron_info = [ request.form.get(k) for k in formnames ] 
        patron_info.append( next_ID_number() )
        dbconn = sqlite3.connect(database)
        db_cursor = dbconn.cursor()
        db_cursor.execute("INSERT INTO donors VALUES(?,?,?,?,?,?,?,?);", patron_info)
        db_cursor.close()
        dbconn.commit()
        dbconn.close()
        return redirect( url_for('review', pid=patron_info[7]) )  
    else:
        return render_template("new.html", ttitle="Contact Information", tpage="/new" )

# ~~~ FIND ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.route("/find", methods = ["GET", "POST"])
def find():
    if request.method == "POST" and request.form.get('donorname'):
        try:
            firstname, lastname = request.form.get('donorname').split(' ')
        except:
            firstname = request.form.get('donorname')
            lastname = ""
        dbconn = sqlite3.connect("donors.db")
        db_cursor = dbconn.cursor()
        pid = db_cursor.execute("SELECT donor_id FROM donors WHERE (firstname = ?) AND (lastname = ?);", (firstname, lastname)).fetchone()
        db_cursor.close()
        dbconn.close()
        if pid:
            return redirect(url_for('review', pid=pid[0]))
        else:
            # This is where we need to inform that the donor can't be found, a new profile needs to be created,
            # And redirect?
            return redirect(url_for('create'))
    else:
        dbconn = sqlite3.connect("donors.db")
        db_cursor = dbconn.cursor()
        db_names = db_cursor.execute("SELECT firstname, lastname FROM donors;").fetchall()
        possible_names = [ f'{name[0]} {name[1]}' for name in db_names ]
        dbconn.close()
        return render_template("find.html", ttitle="Donor Lookup", tpage="/find", tname_possibilities=possible_names)

# ~~~ DONOR ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.route("/donor/<int:pid>", methods = ["GET", "POST"])
def review(pid):
    enable_assign = 'true'
    dbconn = sqlite3.connect(database)
    db_cursor = dbconn.cursor()
    donor_info = db_cursor.execute("SELECT * FROM donors WHERE donor_id = ?;", (pid,)).fetchone()[:7]
    donor_info = dict( zip( ("firstname", "lastname", "street_addr", "city", "state", "zipcode", "email"), donor_info ) )
    fullname = f"{donor_info['firstname']} {donor_info['lastname']}"
    donor_character = db_cursor.execute("SELECT character FROM characters WHERE donor_id = ?;", (pid,)).fetchone()
    if donor_character:
        donor_character = donor_character[0]
        fullname +=  f" (as {donor_character})"
        enable_assign = 'false'
    elif request.method == "POST" and request.form.get('character'):
        charname = request.form.get('character')
        (character, play, pid) = db_cursor.execute("SELECT * FROM characters WHERE (character = ?);", (charname,)).fetchone()
        if not pid:
            pid = db_cursor.execute( "SELECT donor_id FROM donors WHERE firstname = ? AND lastname = ?;",
                    (donor_info['firstname'], donor_info['lastname']) ).fetchone()[0]
            db_cursor.execute("UPDATE characters SET donor_id = ? WHERE character = ?;", (pid, charname))
            fullname += f" (as {charname})"
            enable_assign = 'false'
    play_characters_available = {}
    for (char, play) in db_cursor.execute("SELECT character, play FROM characters WHERE donor_id IS NULL;").fetchall():
        if play not in play_characters_available:
            play_characters_available[play] = []
        play_characters_available[play].append(char)
    play_chars_json = json.dumps(play_characters_available)

    db_cursor.close()
    dbconn.commit()
    dbconn.close()
    return render_template("donor.html", ttitle="Review", tpage=f"/donor/{pid}", tdonor=donor_info, tfullname=fullname, tenableassign=enable_assign,
        tavailchars=play_chars_json)

# ~~~ DONORS LIST ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.route("/list-donors")
def donorlist():
    dbconn = sqlite3.connect(database)
    crs = dbconn.cursor()
    donors = crs.execute("SELECT firstname, lastname, email, donor_id FROM donors;").fetchall()
    donors = [ dict(zip(["firstname", "lastname", "email", "pid"], donor)) for donor in donors ]
    for donor in donors:
        donor['pid'] = int(donor['pid'])
    for donor in donors:
        pid = donor['pid']
        char = crs.execute("SELECT character FROM characters WHERE donor_id = ?;", (pid,)).fetchone()
        if char:
            donor['alias'] = char[0]
        pledge = crs.execute("SELECT pledge FROM pledges WHERE donor_id = ?;", (pid,)).fetchone()
        if pledge:
            donor['pledge'] = int_to_dollar_string(pledge[0])
    crs.close()
    dbconn.close()
    return render_template("donorlist.html", ttitle="List of Donors", tpage="/list-donors", tdonors=donors)

# ~~~ PLEDGE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.route("/pledge", methods = ["GET", "POST"])
def pledge():
    current_tier = "d10k"
    dbconn = sqlite3.connect(database)
    db_cursor = dbconn.cursor()
    assigned_characters = [ c[0] for c in db_cursor.execute("SELECT character FROM characters WHERE donor_id IS NOT NULL;").fetchall() ]
    if request.method == "POST":
        current_tier = request.form.get('current-tier')
        donor_character = request.form.get('donor-alias')
        amount_str = request.form.get('donation-amount')
        if amount_str:
            amount_str = amount_str.translate(str.maketrans( {ord('$'):None, ord(','):None} ))
            if amount_str.isnumeric():
                pledge_amount = int(amount_str)
        if donor_character:
            donor = db_cursor.execute("SELECT donor_id FROM characters WHERE character = ?", (donor_character,) ).fetchone()[0]
            if donor and pledge_amount:

                #  Right here we have to wonder:
                #   1) if this donor has already pledged,  and IF so,
                previous_pledge = db_cursor.execute("SELECT pledge FROM pledges WHERE donor_id = ?;", (donor,)).fetchone()
                if previous_pledge:
                #   2) is this a replacement? or an additional?  pledge?
                    previous_pledge = previous_pledge[0]
                    pledge_amount = previous_pledge if (previous_pledge > pledge_amount) else pledge_amount
                #  (For the moment, we're opting to take the larger of the two)

                db_cursor.execute("INSERT INTO pledges VALUES ( ?, ? );", (donor, pledge_amount))
        elif request.form.get('firstname') and request.form.get('email'):
            donor = next_ID_number()
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            email = request.form['email']
            db_cursor.execute("INSERT INTO donors VALUES ( ?, ?, ?, ?, ?, ?, ?, ? );",
                              (firstname, lastname, None, None, None, None, email, donor))
            if pledge_amount:
                db_cursor.execute("INSERT INTO pledges VALUES ( ?, ? );", (donor, pledge_amount))
    dbconn.commit()
    db_cursor.close()
    dbconn.close()
    return render_template("pledge.html", ttitle="Accept Pledges", tpage="/pledge", tcharlist=assigned_characters, tcurrenttier=current_tier)

# ~~~ CHART ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.route("/chart/update")
@app.route("/chart")
def chart():
    global chart_palette
    dbconn = sqlite3.connect(database)
    crs = dbconn.cursor()
    plays = [ p[0] for p in crs.execute("SELECT DISTINCT play FROM characters;").fetchall() ]
    if not chart_palette:
        chart_palette = generate_palette()
    play_colors = dict( zip( plays, chart_palette[:len(plays)] ) )
    play_amounts = dict([ (play, 0) for play in plays ])
    pledges_so_far = crs.execute("SELECT * FROM pledges WHERE pledge IS NOT NULL;").fetchall()
    for (pid, pledge) in pledges_so_far:
        play = crs.execute("SELECT play FROM characters WHERE donor_id = ?;", (pid,)).fetchone()[0]
        play_amounts[play] += pledge
    play_data = dict( [ (play, { 'amount': play_amounts[play], 'color': play_colors[play] }) for play in reversed(sorted(plays, key=lambda a: play_amounts[a])) ] )
    datajson = json.dumps(play_data)
    crs.close()
    dbconn.close()
    if request.base_url.endswith("/chart/update"):
        return datajson
    else:
        return render_template("chart.html", ttitle="Progress", tpage="/chart", tstartingjson=datajson )

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1')