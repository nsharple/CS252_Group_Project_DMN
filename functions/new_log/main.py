from os import getenv

import pymysql
from pymysql.err import OperationalError

CONNECTION_NAME = getenv(
  'INSTANCE_CONNECTION_NAME',
  'runrecordshare:us-east1:rrs-sql-instance')
DB_USER = getenv('MYSQL_USER', 'root')
DB_PASSWORD = getenv('MYSQL_PASSWORD', '252sqlpassword')
DB_NAME = getenv('MYSQL_DATABASE', 'rrs_database')

mysql_config = {
  'user': DB_USER,
  'password': DB_PASSWORD,
  'db': DB_NAME,
  'charset': 'utf8mb4',
  'cursorclass': pymysql.cursors.DictCursor,
  'autocommit': True
}

# Create SQL connection globally to enable reuse
# PyMySQL does not include support for connection pooling
mysql_conn = None


def __get_cursor():
    """
    Helper function to get a cursor
      PyMySQL does NOT automatically reconnect,
      so we must reconnect explicitly using ping()
    """
    try:
        return mysql_conn.cursor()
    except OperationalError:
        mysql_conn.ping(reconnect=True)
        return mysql_conn.cursor()


def new_log(request):
    global mysql_conn

    # Initialize connections lazily, in case SQL access isn't needed for this
    # GCF instance. Doing so minimizes the number of active SQL connections,
    # which helps keep your GCF instances under SQL connection limits.
    if not mysql_conn:
        try:
            mysql_conn = pymysql.connect(**mysql_config)
        except OperationalError:
            # If production settings fail, use local development ones
            mysql_config['unix_socket'] = f'/cloudsql/{CONNECTION_NAME}'
            mysql_conn = pymysql.connect(**mysql_config)

    parameters = "("

    values = "("

    request_json = request.get_json()
    if request.args and 'email' in request.args:
        parameters += "email"
        values += "\""
        values += request.args.get('email')
        values += "\""
    elif request_json and 'email' in request_json:
        parameters += "email"
        values += "\""
        values += request_json['email']
        values += "\""
    else:
        return "aaaa"

    if request.args and 'date' in request.args:
        parameters += ", date"
        values += ", "
        values += "\""
        values += request.args.get('date')
        values += "\""
    elif request_json and 'date' in request_json:
        parameters += ", date"
        values += ", "
        values += "\""
        values += request_json['date']
        values += "\""
    else:
        return "bbbb"

    distance = None
    if request.args and 'distance' in request.args:
        distance = request.args.get('distance')
    elif request_json and 'distance' in request_json:
        distance = request_json['distance']
    
    if (distance is not None) and (len(distance) > 0):
        parameters += ", distance"
        values += ", " + distance

    time = None
    if request.args and 'time' in request.args:
        time = request.args.get('time')
    elif request_json and 'time' in request_json:
        time = request_json['time']

    if (time is not None) and (len(time) > 0):
        parameters += ", time"
        values += ", \"" + time + "\""

    location = None
    if request.args and 'location' in request.args:
        location = request.args.get('location')
    elif request_json and 'location' in request_json:
        location = request_json['location']

    if (location is not None) and (len(location) > 0):
        parameters += ", location"
        values += ", \"" + location + "\""

    notes = None
    if request.args and 'notes' in request.args:
        notes = request.args.get('notes')
    elif request_json and 'notes' in request_json:
        notes = request_json['notes']

    if (notes is not None) and (len(notes) > 0):
        parameters += ", notes"
        values += ", \"" + notes + "\""

    parameters += ")"

    values += ")"

    query = "INSERT INTO logs " + parameters + " values " + values + ";"

    # Remember to close SQL resources declared while running this function.
    # Keep any declared in global scope (e.g. mysql_conn) for later reuse.

    with __get_cursor() as cursor:
        cursor.execute(query)

    cursor.close()

    headers = {'Access-Control-Allow-Origin': '*'}

    return (query, 200, headers)
