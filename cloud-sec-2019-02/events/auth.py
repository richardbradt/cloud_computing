""" auth.py | Handles all login and registration requests.  With access to the
Users datastore, this script will manage user passwords and accounts. """

from flask import Blueprint, render_template, request, make_response, url_for, redirect, flash
from google.cloud import datastore
from base64 import b64encode
import os, bcrypt, datetime

auth = Blueprint('auth', __name__)
DS = datastore.Client()

""" Handles login functions.  'GET' requests renders login.html.  'POST'
requests handles login procedures.  Checks for user id and password from
Datastore.  Upon success, calls createSession(u_id)"""
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method=='GET':
        return render_template('login.html')
    elif request.method == 'POST':
        # Get Inputs (u_id , pwd)
        u_id = request.form.get('user_id')
        password = (request.form.get('pwd')).encode()

        # Find u_id in Users Datastore
        key = DS.key('Users', u_id)
        entity = DS.query(kind='Users', ancestor=key).fetch()
        for ent in list(entity):
            # hash pwd and compare to Users['password']
            if ent['Username'] == u_id and ent['Password'] == pwd_stretch(password, ent['Password']):
                return createSession(u_id)
            else:
                flash("Username or password is incorrect. Please try again")
                return redirect(url_for('auth.login'))
        else:
            flash("Username or password does not match our records. Please try again")
            return redirect(url_for('auth.login'))
    else:
        console.log('Unexpected request during login: %s' %(request.method))

""" Handles user registration.  'GET' requests renders signup.html. 'POST' handles
form inputs.  Ensures username is not already in Datastore.  Creates new Users
entity, and automatically logins user upon registration with createSession(u_id).

Only instance of data migration using chosen user name: 'first_user'.  This is
used as an example."""
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        # Get input from html form
        u_id = request.form.get('user_id')
        first = request.form.get('f_name')
        last = request.form.get('l_name')
        password = (request.form.get('pwd')).encode()

        # Check for u_id in datastore.  Flash error if found and redirect to signup.
        # Else: add new entity to User datastore. key = User, u_id. Properties
        # are First and Last Name and Hashed password.
        q_key = DS.key('Users', u_id)
        user = DS.query(kind='Users', ancestor=q_key)

        for ent in list(user.fetch()):
            if ent['Username']==u_id:
                flash('Username already exists.  Choose a different username.')
                return redirect(url_for('auth.signup'))

        hashed = pwd_stretch(password)
        with DS.transaction():
            user = datastore.Entity(key=q_key)
            user.update({
                'Username': u_id,
                'First Name': first,
                'Last Name': last,
                'Password': hashed
            })
            DS.put(user)

        # Check for data migration for predetermined user: 'first_user'
        if u_id == 'first_user':
            migrate_data(u_id)

        return createSession(u_id)

    else:
        console.log('Unexpected request during registration: %s' %(request.method))

"""Handles logout function.  Finds session ID using corresponding user key in
datastore.  Deletes entity when found.  Also sets cookies to null values and zero
max_age"""
@auth.route('/logout')
def logout():
    # Delete session ID from datastore
    user = request.cookies.get('user')
    sesh = request.cookies.get('sesh')
    q = DS.query(kind='Session', ancestor=DS.key('Users', user))
    for x in list(q.fetch()):
        if x['Session_ID'] == sesh:
            DS.delete(x.key)
            break

    # Invalidate cookies with null values and zeroed max_age
    flash('You have been signed out.')
    expired = datetime.datetime.now() - datetime.timedelta(hours=1)
    res = make_response(redirect(url_for('auth.login')))
    res.set_cookie('user', '', max_age=0, expires=expired, domain='cloud-sec-2019-02.appspot.com', secure=True)
    res.set_cookie('sesh', '', max_age=0, expires=expired, domain='cloud-sec-2019-02.appspot.com', secure=True)
    return res

"""Handles password stretching for storage.  hash is used for password
comparison"""
def pwd_stretch(pwdStr, hash=None):
    if hash==None:
        return bcrypt.hashpw(pwdStr, bcrypt.gensalt(10))
    else:
        return bcrypt.hashpw(pwdStr, hash)

"""Creates sessions by setting cookies.  Args = user_id | str username.  Deals
with two cookies--'user' and 'session'.  App uses both to verify authentication.
Creates random session id and sets max_age and expires to now()+1 hour."""
def createSession(user_id):
    # Establish variables. Users key.  Random session ID. Expiration date.
    key = DS.key('Users', user_id)
    s_id = b64encode(os.urandom(64)).decode()
    delta = datetime.datetime.now() + datetime.timedelta(hours=1)

    # Add session ID in Datastore under parent User key.
    sesh = datastore.Entity(key=DS.key('Session', parent=key))
    sesh.update({
        'Session_ID': s_id
    })
    DS.put(sesh)

    # Set cookies.
    res = make_response(redirect(url_for('events.root')))
    res.set_cookie('user', user_id, max_age=(60*60), expires=delta, domain='cloud-sec-2019-02.appspot.com', secure=True)
    res.set_cookie('sesh', s_id, max_age=(60*60), expires=delta, domain='cloud-sec-2019-02.appspot.com', secure=True)
    return res

"""Deals with first user data migration.  Args = u_id | username.  Takes known
old entities and transfers under new key from 'first-user'.  Deletes old entities."""
def migrate_data(u_id):
    if u_id == 'first_user':
        old_key = DS.key('Entities', 'root')
        new_key = DS.key('Users', u_id)
        old_q = DS.query(kind='Event', ancestor=old_key)

        for val in list(old_q.fetch()):
            ent = datastore.Entity(key=DS.key('Event', parent=new_key))
            ent.update({
                'Name': val['Name'],
                'Date': val['Date']
            })
            DS.put(ent)
            DS.delete(val.key)   #Delete event under old key
