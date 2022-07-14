from random import Random  				# 用于生成随机码
from django.core.mail import send_mail  # 发送邮件模块
from roomhub import settings		# setting.py添加的的配置信息
from .models import *
import datetime


def SendEmail(email):
	email_title = "HoomHub青年租房管理系统租金支付提醒"
	email_body = "这是一个友好的提醒，您的房间租赁期间快到了,请您即使前往网站缴纳下个月的租金。\n如果已经付款，请忽略此邮件。"
	

	send_status = send_mail(email_title, email_body, settings.EMAIL_HOST_USER, [email])
	return send_status


# 生成随机字符串
def random_str(randomlength=8):
	str = ''
	chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
	length = len(chars) - 1
	random = Random()
	for i in range(randomlength):
		str += chars[random.randint(0, length)]
	return str

def SendCodeEmail(email):
	code = random_str(6)
	NewCode = EmailCode()
	NewCode.code = code
	NewCode.save()
	email_title = "青年租房管理系统注册激活验证码"
	email_body = "欢迎您注册青年租房管理系统!\n"
	email_body += "您的邮箱注册验证码为：{0}, 该验证码有效时间为五分钟，请及时进行验证.\n".format(code)
	email_body += "如果您从未注册过青年租房管理系统,请忽略该邮件."
	send_status = send_mail(email_title, email_body, settings.EMAIL_HOST_USER, [email])
	return send_status


def SendPasswordCodeEmail(email):
	code = random_str(6)
	NewCode = EmailCode()
	NewCode.code = code
	NewCode.save()
	email_title = "青年租房管理系统密码重置验证码"
	email_body = "您的密码重置验证码为：{0}, 该验证码有效时间为五分钟，请及时修改密码.\n".format(code)
	email_body += "如果您从未注册过青年租房管理系统,请忽略该邮件."
	send_status = send_mail(email_title, email_body, settings.EMAIL_HOST_USER, [email])
	return send_status

def CheckCode(code):
	if EmailCode.objects.filter(code=code).exists() == False:
		return False
	else:
		EmailCode.objects.filter(code=code).delete()
		return True

def SendSEmail(email):

	email_title = "青年租房管理系统审核信息"
	email_body = "您的租房申请已通过，感谢您对HommHub青年租房管理系统的支持，请您及时到网站查看相关信息.\n"
	email_body += "如果您从未注册过青年租房管理系统,请忽略该邮件."
	send_status = send_mail(email_title, email_body, settings.EMAIL_HOST_USER, [email])
	return send_status


def SendFEmail(email):
	email_title = "青年租房管理系统审核信息"
	email_body = "您的租房申请未通过，请您仔细检查相关信息是否填写无误，感谢您对HommHub青年租房管理系统的支持\n"
	email_body += "如果您从未注册过青年租房管理系统,请忽略该邮件."
	send_status = send_mail(email_title, email_body, settings.EMAIL_HOST_USER, [email])
	return send_status