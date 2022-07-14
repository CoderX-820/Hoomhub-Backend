"""
WSGI config for roomhub project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roomhub.settings')

application = get_wsgi_application()

import uwsgi
import time
from roomhubSite.models import *
import datetime
from roomhubSite.email_send import *
from dateutil.relativedelta import relativedelta

def time(signum):
    contracts=RContract.objects.all()
    day=datetime.date.today()
    for i in contracts:
        for j in range(1,15):
            nday=i.start_time + relativedelta(months=j)
            if (i.end_time-day).days>=0 and (day-i.start_time).days>=0 and ((day-i.start_time).days + 7) == ((nday-i.start_time).days):
                send_result = SendEmail(i.Email)
                break
# def cron_print_hello(signum):
#     print("hello")

jobs = [ { "name" : time,
           "time": [0, 8, -1, -1, -1], #minute, hour, day, month, weekday, "-1" means "all"，此例为每个周一的17：00
          },     
        #  { "name" : cron_print_hello,
        #    "time": [2],  #每隔2秒
        #   },    
]

for job_id, job in enumerate(jobs):
    uwsgi.register_signal(job_id, "", job['name'])
    if len(job['time']) == 1:
        uwsgi.add_timer(job_id, job['time'][0])
    else:
        uwsgi.add_cron(job_id, job['time'][0], job['time'][1], job['time'][2], job['time'][3], job['time'][4])