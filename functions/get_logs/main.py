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


def get_logs(request):
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return ('', 204, headers)

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

    query = "SELECT * FROM logs WHERE email='" + email + "';"
    with __get_cursor() as cursor:
        cursor.execute(query)
        result = ""
        for row in cursor:

            # Header
            result += "<div class=\"list-group-item list-group-item-action py-0\"><div class=\"row\">"

			# Date
            result += "<div class=\"col-md-2 text-center align-self-center h6 p-4\">"
            result += str(row["date"])

			# Distance
            result += "</div><div class=\"col border-left\"><div class=\"row border-bottom\"><div class=\"border-right p-2 px-3\"><span class=\"h6\">Distance: </span><span>"
            result += str(row.get('distance')) if row.get('distance')  else "-"

			# Time
            result += "</span></div><div class=\"col p-2 px-3\"><span class=\"h6\">Time: </span><span>"
            result += str(row.get('time')) if (row.get('time')) else "-"
            result += "</span>"

            # Delete Button
            result += "<a class=\"btn btn-dark pull-right bg-danger btn-sm\" onclick=\"\" role=\"button\" log_id=\""
            result += str(row.get('log_id'))
            result += "\"><i class=\"fa fa-times\"></i></a>"

			# Location
            result += "</div></div><div class=\"row border-bottom\"><div class=\"col p-2 px-3\"><span class=\"h6\">Location: </span><span>"
            result += row.get('location') if row.get('location') else "-"

			# Additional Notes
            result += "</span></div></div><div class=\"row\"><div class=\"col p-2 px-3\"><span class=\"h6\">Additional Notes: </span><span>"
            result += row.get('notes') if row.get('notes') else "-"

			# Rest
            result += "</span></div></div></div></div></div>"

    headers = {'Access-Control-Allow-Origin': 'https://runrecordshare.appspot.com'}

    return (result, 200, headers)
