from flask import Flask

class NotAuthException(Exception):
	pass

class ContactWithAdmException(Exception):
	pass