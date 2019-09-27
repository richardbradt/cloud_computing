from flask import Blueprint, render_template, request, make_response, redirect, url_for, flash
from google.cloud import datastore
from functools import wraps
import datetime

events = Blueprint('events', __name__)

DS = datastore.Client()
EVENT = 'Event'
key_dict = {}

"""Decorator used to wrap all functions that require user login."""
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = request.cookies.get('user')
        sesh_id = request.cookies.get('sesh')

        if user_id:
            # Check user_id and session ID in Datastore
            q_key = DS.key('Sessions', sesh_id)
            q = DS.query(kind='Sessions', ancestor=q_key).fetch()

            for val in list(q):
                if val['exp'].replace(tzinfo=None)<=datetime.datetime.now() or user_id!=val['user']:
                    # Check user and expiration under Session in Datastore
                    flash('Expired Session')
                    return redirect(url_for('auth.logout'))
                else:
                    return func(*args, **kwargs)
        else:
            flash("Please log in")
            return redirect(url_for('auth.login'))

        flash('Session Error: Unmatched user session')
        return redirect(url_for('auth.login'))

    return wrapper

"""Root URL.  Renders HTML and returns events data."""
@events.route('/')
@login_required
def root():
    user_id = request.cookies.get('user')
    f_name = DS.get(DS.key('Users', user_id))['name']

    return render_template('events.html', data=send_events_to_jscript(), name=f_name)

"""Handles GET reqeusts to /events URL.  Retruns events JSON. Queries Datastore
for Entities in database.  Stores Name and Date properties and Entity key.
Creates and Event JSON consisting of Name, Date, and ID."""
@events.route('/events', methods=['GET'])
@login_required
def send_events_to_jscript():
    # Queary database for events and create event list.
    u_id = request.cookies.get('user')
    p_key = DS.key('Users', u_id)
    QUERY = DS.query(kind=EVENT, ancestor=p_key)
    entity_list = []
    for val in list(QUERY.fetch()):
        entity_list.append((val['Name'],val['Date'],val.key))
    # Sort list of events by date.
    entity_list.sort(key=lambda index: index[1])

    # Create events JSON.  Provide each event a unique ID and add keys to dict.
    if len(entity_list) < 1:
        event_json = '{"events":[]}'
        return event_json
    else:
        event_json = '{"events":['
        counter = 1
        eventID = ''
        for x in entity_list:
            eventID = 'Event%d'%(counter)
            if counter==len(entity_list):
                event_json+='{"Name":"'+x[0]+'","Date":"'+x[1]+'","ID":"'+eventID+'"}]}'
                key_dict[eventID] = '%s'%(x[2])
                break
            else:
                event_json+='{"Name":"'+x[0]+'","Date":"'+x[1]+'","ID":"'+eventID+'"},'
                key_dict[eventID] = '%s'%(x[2])
                counter+=1

        return event_json

"""Handles POST reqeust with /event URL.  Adds events to database.  Requests
JSON from AJAX call. Returns new event."""
@events.route('/event', methods=['POST'])
@login_required
def add_event():
    u_id = request.cookies.get('user')
    p_key = DS.key('Users', u_id)
    # Get JSON from AJAX call
    new_json = request.get_json()
    # Add new entity to database.
    entity = datastore.Entity(key=DS.key(EVENT, parent=p_key))
    entity.update({'Name': new_json['Name'], 'Date': new_json['Date']})
    DS.put(entity)
    return new_json

"""Handles POST request with /delete URL.  Deletes events from database.
Requests JSON from AJAX call.  Uses EventID to find corresponding key in the
key dictionary.  Returns events JSON."""
@events.route('/delete', methods=['POST'])
@login_required
def del_event():
    u_id = request.cookies.get('user')
    p_key = DS.key('Users', u_id)
    QUERY = DS.query(kind=EVENT, ancestor=p_key)
    # Get JSON from AJAX call
    del_json = request.get_json()
    # Query database for keys.  Compare with EventID:key pair in dictionary.
    for ent in list(QUERY.fetch()):
        key_str = '%s'%ent.key
        if key_str in key_dict[del_json['ID']]:
            DS.delete(ent.key)
            key_dict.pop(del_json['ID'])
            break
        else:
            continue
    return send_events_to_jscript()
