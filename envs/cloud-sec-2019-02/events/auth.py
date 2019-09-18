""" auth.py | Handles all login and registration requests.  With access to the
Users datastore, this script will manage user passwords and accounts. """

from flask import Blueprint, render_template, request, url_for, redirect, flash, session
from google.cloud import datastore
import bcrypt

auth = Blueprint('auth', __name__)
DS = datastore.Client()

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
            # if match, set session['user_id'] = u_id
            # return redirect(url_for('events.root'))
            if ent['Username'] == u_id and ent['Password'] == pwd_stretch(password, ent['Password']):
                session['user_id'] = u_id
                return redirect(url_for('events.root'))
            else:
                flash("Username or password is incorrect. Please try again")
                return redirect(url_for('auth.login'))
        else:
            flash("Username or password does not match our records. Please try again")
            return redirect(url_for('auth.login'))
    else:
        console.log('Unexpected request during login: %s' %(request.method))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        pass
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
        # After adding user.  Automatically login with new user.
        session['user_id'] = u_id
        return redirect(url_for('events.root'))
    else:
        console.log('Unexpected request during registration: %s' %(request.method))


@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been signed out.')
    return redirect(url_for('auth.login'))

def pwd_stretch(pwdStr, hash=None):
    if hash==None:
        return bcrypt.hashpw(pwdStr, bcrypt.gensalt(10))
    else:
        return bcrypt.hashpw(pwdStr, hash)
