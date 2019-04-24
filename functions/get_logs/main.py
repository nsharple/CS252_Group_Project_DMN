#def hello_world(request):
#    """Responds to any HTTP request.
#    Args:
#        request (flask.Request): HTTP request object.
#    Returns:
#        The response text or any set of values that can be turned into a
#        Response object using
#        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
#    """

#    request_json = request.get_json()
#    if request.args and 'message' in request.args:
#        return "args: " + request.args.get('message')
#    elif request_json and 'message' in request_json:
#        return "json: " + request_json['message']
#    else:
#        return f'Hello World!'


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


def mysql_demo(request):
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

    request_json = request.get_json()
    if request.args and 'email' in request.args:
        email = request.args.get('email')
    elif request_json and 'email' in request_json:
        email = request_json['email']
    else:
        return ""

    # Remember to close SQL resources declared while running this function.
    # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
    with __get_cursor() as cursor:
        cursor.execute("SELECT * FROM logs WHERE email=" + email)
        result = ""
        for row in cursor:
            result += str(row)
        return result