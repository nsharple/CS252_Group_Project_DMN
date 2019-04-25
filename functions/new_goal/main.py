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

    if request.args and 'coachEmail' in request.args:
        parameters += ", coach_email"
        values += ", "
        values += "\""
        values += request.args.get('coachEmail')
        values += "\""
    elif request_json and 'coachEmail' in request_json:
        parameters += ", coach_email"
        values += ", "
        values += "\""
        values += request_json['coachEmail']
        values += "\""
    else:
        return ""

    if request.args and 'type' in request.args:
        parameters += ", type"
        values += ", "
        if request.args.get('type') == "Distance":
            values += "d"
        elif request.args.get('type') == "Time":
            values += "t"
        else:
            values += "n"
    elif request_json and 'type' in request_json:
        parameters += ", type"
        values += ", "
        if request_json['type'] == "Distance":
            values += "d"
        elif request_json['type'] == "Time":
            values += "t"
        else:
            values += "n"
    else:
        return ""

    if request.args and 'start_date' in request.args:
        parameters += ", start_date"
        values += ", "
        values += "\""
        values += request.args.get('start_date')
        values += "\""
    elif request_json and 'start_date' in request_json:
        parameters += ", start_date"
        values += ", "
        values += "\""
        values += request_json['start_date']
        values += "\""
    else:
        return ""

    if request.args and 'end_date' in request.args:
        parameters += ", end_date"
        values += ", "
        values += "\""
        values += request.args.get('end_date')
        values += "\""
    elif request_json and 'end_date' in request_json:
        parameters += ", end_date"
        values += ", "
        values += "\""
        values += request_json['end_date']
        values += "\""
    else:
        return ""

    if request.args and 'distance' in request.args:
        distance = request.args.get('distance')
    elif request_json and 'distance' in request_json:
        distance = request_json['distance']

    if (distance is not None) and (len(distance) > 0):
        parameters += ", distance"
        values += ", " + distance

    if request.args and 'time' in request.args:
        time = request.args.get('time')
    elif request_json and 'time' in request_json:
        time = request_json['time']

    if (time is not None) and (len(time) > 0):
        parameters += ", time"
        values += ", \"" + time + "\""

    if request.args and 'numruns' in request.args:
        nruns = request.args.get('numruns')
    elif request_json and 'numruns' in request_json:
        nruns = request_json['numruns']

    if (nruns is not None) and (len(nruns) > 0):
        parameters += ", numruns"
        values += ", \"" + nruns + "\""

    if request.args and 'notes' in request.args:
        notes = request.args.get('notes')
    elif request_json and 'notes' in request_json:
        notes = request_json['notes']

    if (notes is not None) and (len(notes) > 0):
        parameters += ", notes"
        values += ", \"" + notes + "\""

    parameters += ")"

    values += ")"

    query = "INSERT INTO goals " + parameters + " VALUES " + values + ";"

    # Remember to close SQL resources declared while running this function.
    # Keep any declared in global scope (e.g. mysql_conn) for later reuse.

    with __get_cursor() as cursor:
        cursor.execute(query)