from jwt import encode
from jwt import decode
import datetime
from .models import *

def GetToken(email):
	time = datetime.datetime.now()
	return encode({'email':email, 'logintime': str(time), 'id':UserInfo.objects.get(email=email).userID
		}, 'secret_key', algorithm='HS256')

def Check(token):
	try:
		s = decode(token,  'secret_key', algorithms=['HS256'])
	except:
		return -1
	return s.get('id',-1)

