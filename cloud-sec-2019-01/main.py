from flask import Flask, render_template, request
from google.cloud import datastore

app = Flask(__name__)

DS = datastore.Client()
EVENT = 'Event'
ROOT = DS.key('Entities', 'root')
QUERY = DS.query(kind=EVENT, ancestor=ROOT)
key_dict = {}

"""Root URL.  Renders HTML and returns events data."""
@app.route('/')
def root():
    return render_template('index.html', data=send_events_to_jscript())

"""Handles GET reqeusts to /events URL.  Retruns events JSON. Queries Datastore
for Entities in database.  Stores Name and Date properties and Entity key.
Creates and Event JSON consisting of Name, Date, and ID."""
@app.route('/events', methods=['GET'])
def send_events_to_jscript():
    # Queary database for events and create event list.
    entity_list = []
    for val in list(QUERY.fetch()):
        entity_list.append((val['Name'],val['Date'],val.key))
    # Sort list of events by date.
    entity_list.sort(key=lambda index: index[1])
    # Create events JSON.  Provide each event a unique ID and add keys to dict.
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
@app.route('/event', methods=['POST'])
def add_event():
    # Get JSON from AJAX call
    new_json = request.get_json()
    # Add new entity to database.
    entity = datastore.Entity(key=DS.key(EVENT, parent=ROOT))
    entity.update({'Name': new_json['Name'], 'Date': new_json['Date']})
    DS.put(entity)
    return new_json

"""Handles POST request with /delete URL.  Deletes events from database.
Requests JSON from AJAX call.  Uses EventID to find corresponding key in the
key dictionary.  Returns events JSON."""
@app.route('/delete', methods=['POST'])
def del_event():
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

if __name__ == '__main__':
    # Run the app during local testing
    app.run(host='127.0.0.1', port=8080, debug=True)
