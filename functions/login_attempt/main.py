import cgi

def login_attempt(request):
	"""Responds to an HTTP request to sign in to the website.
	Args:
		request (flask.Request): HTTP request object.
	Returns:
		WHAT TO PUT HERE???
	"""
	request_json = request.get_json(silent=True)
	request_args = request.args

	formData = cgi.FieldStorage()
	email = formData.getValue('email')
	return format(email)

	if request_json and 'email' in request_json and 'password' in request_json:
		return request_json['email'] + "\n" + request_json['password']
	elif request_args and 'email' in request_args and 'password' in request_args:
		return f'This still works'
	else:
		return f'Hello World!'
