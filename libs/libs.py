from flask import Flask, request, render_template, session
from flask import send_from_directory, url_for, redirect
import urllib2 as h2
import urllib as h
import json
import exceptions
import constants

def select_keys(request={}, l=[]):
    return dict((k,v) for (k,v) in request.items() if k in l)


def make_request(method="get", server_url="", params={}):
	#print "<-  m:" + method + ", server_url:" + str(server_url) + ", params:" + str(params)
	response={}
	try:
		if method.lower()=="get":
			set_params="?" + "&".join("%s=%s" % (k,v) for k,v in params.items()) if params else ""
			server_response=json.loads(h2.urlopen(server_url + set_params).read())
		else:
			server_response=json.loads(h2.urlopen(server_url, h.urlencode(dict(params))).read())

	except Exception, inst:
		response['error'] = str(inst)
		return response

	if server_response.get('success'):
		response['data']=dict((k,v) for k,v in server_response.items() if not k in set(['success', 'error', 'error_description']))
	else:
		if 'error' in server_response:
			if server_response.get('error') == constants.ERRORS.not_auth:	
				raise exceptions.NotAuthException('')
				
			if 'error_description' in server_response:
				response['error'] = 'Error: "%s", Error details: "%s"' % (server_response['error'], server_response['error_description'])
			else:
				response['error'] = 'Error: "%s"' % server_response['error']
			
		else:
			response['error']='Error not defined'

	return response


def logout_by_token(token):
    return make_request(server_url='https://goods.itvik.com/api/logout/', method="post", params={'token':token})
