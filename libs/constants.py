class Constants(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
            
ERRORS = Constants(
    invalid_request='invalid request',
    user_not_found='user not found',
    not_auth='not authenticated',
    already_registered='already registered',
    already_changed='already changed',
    unknown_error='unknown error')

