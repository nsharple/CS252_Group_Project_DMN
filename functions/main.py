def login_attempt(request):
	"""Responds to an HTTP request to sign in to the website.
	Args:
		request (flask.Request): HTTP request object.
	Returns:
		WHAT TO PUT HERE???
	"""
	request_json = request.get_json()
	if request.args and 'email' in request.args and 'password' in request.args:
		return request.args.get('email') + request.args.get('password')
	elif request_json and 'email' in request_json:
		return request_json['email']
	else:
		return f'Hello World!'
