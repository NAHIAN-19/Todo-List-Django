from rest_framework.authtoken.models import Token

def import_rest_framework_token():
    try:
        Token
    except NameError:
        from rest_framework.authtoken.models import Token
