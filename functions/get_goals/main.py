from os import getenv

import datetime

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


def get_goals(request):
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

    query = "SELECT * FROM goals WHERE email='" + email + "';"
    with __get_cursor() as cursor:
        cursor.execute(query)
        result = ""
        for row in cursor:

            # Calculations for progression and percentage
            percentage = 0.0
            distTotal = 0.0
            timeTotal = 0.0
            runTotal = 0
            query2 = "SELECT * FROM logs WHERE email='" + email + "' AND date>='" + str(row.get('start_date')) + "' AND date<='" + str(row.get('end_date')) + "';"
            with __get_cursor() as cursor2:
                cursor2.execute(query2)
                for row2 in cursor2:
                    distTotal += row2.get('distance') if row2.get('distance') else 0
                    timeTotal += row2.get('time').total_seconds() if row2.get('time') else 0
                    runTotal += 1

                timeTotal = timeTotal / 3600.0

            cursor2.close()

            # Header
            item = "<div class=\"list-group-item list-group-item-action py-0 border-bottom\""
            if str(row.get('end_date')) < str(str(datetime.datetime.today()).split()[0]):
                item += "style=\"opacity:0.6; background-color:Gray;\""

            # Progression
            item += "><div class=\"row\"><div class=\"col-md-2 p-4\"><div class=\"align-self-center text-center h1\">"
            if row.get('type') == 'D':
                item += str(distTotal)
                percentage = distTotal / row.get('distance')
            elif row.get('type') == 'T':
                item += "{0:.2f}".format(timeTotal)
                percentage = timeTotal / row.get('time')
            else:
                item += str(runTotal)
                percentage = runTotal / row.get('num_runs')
            percentage = percentage * 100
            percentage = 100.0 if percentage > 100 else percentage

            # Total Goal
            goalLabel = "";
            item += "</div><div class=\"align-self-center text-center h6\">out of "
            if row.get('type') == 'D':
                item += str(row.get('distance'))
                goalLabel = " miles"
            elif row.get('type') == 'T':
                item += str(row.get('time'))
                goalLabel = " hours"
            else:
                item += str(row.get('num_runs'))
                goalLabel = " runs"
            item += goalLabel

            # Progress Bar
            item += "</div></div><div class=\"col border-left\"><div class=\"row border-bottom\"><div class=\"col p-2 px-3\"><div class=\"progress\">"
            item += "<div class=\"progress-bar progress-bar-striped "
            item += "bg-success" if percentage == 100 else "bg-primary"
            item += "\" role=\"progressbar\" style=\"width: "
            item += "{0:.2f}".format(percentage)
            item += "%\" aria-valuenow=\""
            item += "{0:.2f}".format(percentage)
            item += "\" aria-valuemin=\"0\" aria-valuemax=\"100\">"
            item += "{0:.2f}".format(percentage)
            item += "%</div></div></div></div>"

            # Coach Email
            item += "<div class=\"row border-bottom\"><div class=\"border-right p-2 px-3\"><span class=\"h6\">Given by: </span><span>"
            item += row.get('coach_email') if row.get('coach_email') else "Yourself"
            item += "</span></div>"

            # Start Date
            item += "<div class=\"border-right p-2 px-3\"><span class=\"h6\">From: </span><span>"
            item += str(row.get('start_date'))
            item += "</span></div>"

            # End Date
            item += "<div class=\"p-2 px-3\"><span class=\"h6\">To: </span><span>"
            item += str(row.get('end_date'))
            item += "</span></div></div>"

            # Additional Notes
            item += "<div class=\"row\"><div class=\"col p-2 px-3\"><span class=\"h6\">Additional Notes: </span><span>"
            item += row.get('notes') if row.get('notes') else "-"
            item += "</span>"

            # Delete Button
            item += "<a class=\"btn btn-dark pull-right bg-danger btn-sm\" role=\"button\" onclick=\"deleteEntry("
            item += str(row.get('goal_id'))
            item += ", 'goal')\"><i class=\"fa fa-times\"></i></a>"

            # Finish
            item += "</div></div></div></div></div>"

            result = item + result

    cursor.close()

    headers = {'Access-Control-Allow-Origin': '*'}

    return (result, 200, headers)

