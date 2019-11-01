"""App that produced a path count."""
"""Default route will increment count for each path and store data in database."""

from flask import Flask, request, render_template
from os.path import join, dirname
from dotenv import load_dotenv
import json, os, psycopg2

"""Import Environment Variables for DB"""
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

user = os.getenv('POSTGRES_USER')
db = os.getenv('POSTGRES_DATABASE')
secret = os.getenv('POSTGRES_PASSWORD')
host = os.getenv('POSTGRES_HOST')

app = Flask(__name__)

"""Default route will get path and check for database entry"""
"""If in database, increment count. If not, set count to 1 and add to db"""
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def root(path):
    c_path = request.path
    print('CURRENT PATH: {}'.format(c_path))
    count_path(c_path)
    return display_paths()

"""Check database for path and count"""
"""Add connection to Postgresql database"""
def count_path(path):
    sql = """INSERT INTO pathcount (path, count)
                VALUES (%s, 1)
             ON CONFLICT (path) DO UPDATE
                SET count = pathcount.count + 1
             RETURNING count;"""
    conn = None
    new_count = None

    try:
        conn = psycopg2.connect(host=host ,database=db, user=user, password=secret)
        cur = conn.cursor()
        cur.execute(sql, (path,))
        new_count = cur.fetchone()[0]
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

"""Display current database contents"""
"""Add query of Postgresql database"""
def display_paths():
    sql = """SELECT path, count FROM pathcount ORDER BY path"""
    conn = None

    try:
        conn = psycopg2.connect(host=host ,database=db, user=user, password=secret)
        cur = conn.cursor()
        cur.execute(sql)
        entities = cur.fetchall()
        path_json = build_json(entities)
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

    return render_template('index.html', data=path_json)

"""Builds JSON to send to HTML/JS.  Takes entity list from DB"""
def build_json(path_list):
    new_json = '['
    counter = 1
    for ent in path_list:
        print("CURRENT KEY: {}".format(ent[0]))
        print("CURRENT KEY VALUE: {}".format(ent[1]))
        if counter==len(path_list):
            new_json+='{"path":"%s","count":"%d"}]' % (ent[0], ent[1])
            break
        else:
            new_json+='{"path":"%s","count":"%d"},' % (ent[0], ent[1])
            counter+=1

    return new_json

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080')
