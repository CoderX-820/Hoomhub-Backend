from django.http import JsonResponse
from django.shortcuts import render
from .models import *
import json
from django.http import HttpResponse
from .email_send import *
from .token import *
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
import re
from datetime import date,timezone
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import random
import time,os
from django.http import FileResponse
from pathlib import Path
from concurrent import futures
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, \
    PageBreak, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet, LineStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from roomhub import settings	

pdfmetrics.registerFont(TTFont('msyh', '/usr/share/fonts/msyh/msyh.ttc'))

@csrf_exempt
def register(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        username = data_json.get('username')
        password = data_json.get('password')
        email = data_json.get('email')
        role = data_json.get('role')
        code = data_json.get('code')
        if UserInfo.objects.filter(email=email).exists():
            return JsonResponse({'result': 0, 'message': "邮箱已注册!"})
        else:
            if EmailCode.objects.filter(code=code).exists() == False:
                return JsonResponse({'result': 0, 'message': "验证码错误!"})
            emailcode=EmailCode.objects.get(code=code)
            now=datetime.datetime.now(timezone.utc)

            if (now - emailcode.time).seconds>300:
                return JsonResponse({'result': 0, 'message': "验证码已失效!"})    
            all = UserInfo.objects.all()
            count = len(all)
            new_user = UserInfo(userID=count, username=username,
                                password=password, email=email, role=role)
            new_user.save()
        return JsonResponse({'result': 1, 'message': "注册成功!"})
    else:
        return JsonResponse({'result': 0, 'message': "前端炸了!"})


@csrf_exempt
def login(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        email = data_json.get('email')
        password = data_json.get('password')
        if len(email) == 0 or len(password) == 0:
            result = {'result': 0, 'message': '邮箱与密码不允许为空!'}
        else:
            if UserInfo.objects.filter(email=email).exists() == False:
                result = {'result': 0, 'message': '邮箱未注册!'}
            else:
                user = UserInfo.objects.get(email=email)
                if user.password != password:
                    result = {'result': 0, 'message': '密码不正确!'}
                else:
                    request.session['email'] = email
                    result = {'result': 1, 'message': '登录成功!','username':user.username}
                    token = GetToken(email)
                    result['token'] = token
                    request.session['token'] = token
                    result['id'] = user.userID
                    result['role'] = user.role
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了'}
        return JsonResponse(result)


@csrf_exempt
def email(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        Email = data_json.get('email')
        if Email.count('@') == 1:
            send_result = SendEmail(Email)
            if send_result == False:
                result = {'result': 0, 'message': '发送失败!请检查邮箱格式'}
            else:
                result = {'result': 1, 'message': '发送成功!'}
                return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '邮箱格式不正确!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)




@csrf_exempt
def email_register(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        Email = data_json.get('email')
        if Email.count('@') == 1:
            send_result = SendCodeEmail(Email)
            if send_result == False:
                result = {'result': 0, 'message': '发送失败!请检查邮箱格式'}
            else:
                result = {'result': 1, 'message': '发送成功!请及时在邮箱中查收.'}
                return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '邮箱格式不正确!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def email_forget(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        Email = data_json.get('email')
        if Email.count('@') == 1:
            send_result = SendPasswordCodeEmail(Email)
            if send_result == False:
                result = {'result': 0, 'message': '发送失败!请检查邮箱格式'}
            else:
                result = {'result': 1, 'message': '发送成功!请及时在邮箱中查收.'}
                return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '邮箱格式不正确!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def forgetpassword(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        email = data_json.get('email', 'null')
        if UserInfo.objects.filter(email=email).exists():
            user = UserInfo.objects.get(email=email)
            code = data_json.get('code')
            if EmailCode.objects.filter(code=code).exists() == False:
                result = {'result': 0, 'message': '验证码错误!'}
                return JsonResponse(result)
            emailcode=EmailCode.objects.get(code=code)
            now=datetime.datetime.now(timezone.utc)
            if (now - emailcode.time).seconds>300:
                return JsonResponse({'result': 0, 'message': "验证码已失效!"})  
            emailcode.delete()
            password = data_json.get('password')
            user.password = password
            user.save()
            result = {'result': 1, 'message': '修改成功!'}
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '不存在该用户!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def logout(request):
    request.session.flush()

@csrf_exempt
def changepassword(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        password=data_json.get('password')
        n_password=data_json.get('n_password')
        user=UserInfo.objects.get(userID=id)
        if(user.password==password):
            user.password=n_password
            user.save()
            result = {'result': 1, 'message': '修改成功!'}
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '密码不正确!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
def uploadinfo(request):  # 修改用户基础信息
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user = UserInfo.objects.get(userID=id)
        user.sex = int(data_json.get('sex'))
        user.telephone= data_json.get('telephone')
        user.username= data_json.get('username')
        email= data_json.get('email')
        user.birth= data_json.get('birth')
        user.CardID= data_json.get('CardID')
        user.summary= data_json.get('summary')
        if email==user.email:
            user.email= data_json.get('email')
            user.save()
            result = {'result': 1, 'message': '修改成功!'}
            return JsonResponse(result)
        if UserInfo.objects.filter(email=email).exists():
            result = {'result': 0, 'message': '邮箱已注册!'}
            return JsonResponse(result)
        else:
            user.email= data_json.get('email')
            user.save()
            result = {'result': 1, 'message': '修改成功!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def getuser(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user = UserInfo.objects.get(userID=id)

        result = {'result': 1, 'message': '查询成功!', 'name': user.username, 'id': id,
                  'url': user.get_photo_url, 'email': user.email, 'role': user.role,'money':user.money,'telephone':user.telephone,'birth':user.birth,'summary':user.summary,'sex':user.sex,'username':user.username,'CardID':user.CardID}
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def upload_avatars(request):  # 修改头像
    if request.method == 'POST':
        # data_json = json.loads(request.body)
        token = request.POST.get('token')
        # token = request.META.get('HTTP_AUTHORIZATION', 0)
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        source = request.FILES.get('file')
        if source:
            if UserInfo.objects.filter(userID=id).exists() == True:
                user = UserInfo.objects.get(userID=id)
                user.header = source
                user.save()
                result = {'result': 1, 'id': id,  'url': user.get_photo_url}
            else:
                result = {'result': 0, 'message': '未找到该用户!'}
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '请检查上传内容!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def room_add(request):  # 发布房源及权限识别
    if request.method == 'POST':
        token = request.META.get('HTTP_AUTHORIZATION', 0)
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user = UserInfo.objects.get(userID=id)
        if(user.role != 1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result)
        else:
            name = request.POST.get('title')
            category = request.POST.get('category')
            status = request.POST.get('status')
            house_size = int(request.POST.get('house_size'))
            price = int(request.POST.get('price'))
            address = request.POST.get('address')
            type = request.POST.get('type')
            is_near_subway = int(request.POST.get('is_near_subway'))
            is_has_dw = int(request.POST.get('is_has_dw'))
            is_has_yt = int(request.POST.get('is_has_yt'))
            style= request.POST.get('style')  
            summary= request.POST.get('summary')
            rules= request.POST.get('rules')
            bed=int(request.POST.get('bed'))
            images = request.FILES.getlist('file')
            HouseID = len(RHouse.objects.all())
            for source in images:
                RImg.objects.create(HouseID=HouseID, img=source)
            RHouse.objects.create(HouseID=HouseID, name=name, category=category, status=status,
                                    house_size=house_size, price=price, address=address, type=type, is_near_subway=is_near_subway, is_has_dw=is_has_dw, is_has_yt=is_has_yt, total_views=0,style=style,summary=summary,rules=rules,bed=bed)
            result = {'result': 1, 'message': '房源发布成功'}
            return JsonResponse(result)


def fix(request):  # 房源状态改变
    if request.method == 'POST':
        token = request.META.get('HTTP_AUTHORIZATION', 0)
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user = UserInfo.objects.filter(userid=id)
        if(user.role != 1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result)
        else:
            data_json = json.loads(request.body)
            HouseID = int(data_json.get('HouseID'))
            House = RHouse.objects.filter(HouseID=HouseID)
            if RHouse.objects.filter(HouseID=HouseID).exists() == True:
                House = RHouse.objects.filter(HouseID=HouseID)
                House.status = data_json.get('status')
                House.save()
                result = {'result': 1, 'message': '状态更改成功'}
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '未找到该房间'}
                return JsonResponse(result)


@csrf_exempt
def upload_image(request):  # 上传图片
    if request.method == 'POST':
        token = request.META.get('HTTP_AUTHORIZATION', 0)
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user = UserInfo.objects.get(userID=id)
        if(user.role != 1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result)
        else:
            HouseID = int(request.POST.get('HouseID'))
            if RHouse.objects.filter(HouseID=HouseID).exists() == True:
                source = request.FILES.get('file')
                image = RImg(HouseID=HouseID, img=source)
                image.save()
                result = {'result': 1, 'message': '上传成功','id': image.imgid, 'url': 'http://43.138.77.8/dz/roomhubSite'+image.img.url,}
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '未找到该房间'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def delete_image(request):  # 删除图片
    if request.method == 'POST':
        token = request.META.get('HTTP_AUTHORIZATION', 0)
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user = UserInfo.objects.get(userID=id)
        if(user.role != 1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result)
        else:
            data_json = json.loads(request.body)
            imgid = int(data_json.get('imgid'))
            if RImg.objects.filter(imgid=imgid).exists() == True:
                image = RImg.objects.get(imgid=imgid)
                image.delete()
                result = {'result': 1, 'message': '删除成功'}
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '未找到该房间'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def allhouse(request):  # 查询所有房间
    if request.method == 'POST':
        token = request.META.get('HTTP_AUTHORIZATION', 0)
        id = Check(token)
        if id == -1:
            result = {'result': 1, 'message': 'Token有误!'}
            all = RHouse.objects.filter(status="正常出售")
            house = []
            for i in all:
                d = {}
                d["HouseID"] = i.HouseID
                d["price"] = i.price
                d["name"] = i.name
                d["type"] = i.type
                d["style"] = i.style
                d["address"] = i.address
                d["house_size"] = i.house_size
                d["category"] = i.category
                d["is_near_subway"] = i.is_near_subway
                d["is_has_dw"] = i.is_has_dw
                d["is_has_yt"] = i.is_has_yt
                d["total_views"] = i.total_views
                d["is_collect"]=0
                if RImg.objects.filter(HouseID=i.HouseID).exists() == True:
                    imgs = RImg.objects.filter(HouseID=i.HouseID)
                    d["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url
                else:
                    d["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"
                if(i.type=="短租"):
                    begin = date.today()
                    end=begin + timedelta(days=30)
                    exist = Order.objects.filter(HouseID=i.HouseID).first()
                    s=""
                    if exist:
                        order = Order.objects.filter(HouseID=i.HouseID)
                        for j in range((end - begin).days+1):
                            day = begin + datetime.timedelta(days=j)
                            sign=0
                            for k in order:
                                start=k.start_time
                                end=k.end_time
                                if start<=day<=end:  
                                    sign=1
                                    break
                            if sign==1:
                                s+='1'    
                            else:
                                s+='0'                            
                    else:
                        s="000000000000000000000000000000"           
                else:
                    begin = date.today()
                    end=begin + relativedelta(months=12)
                    exist = Order.objects.filter(HouseID=i.HouseID).first()
                    s=""
                    if exist:
                        order = Order.objects.filter(HouseID=i.HouseID)
                        for j in range(0,12):
                            day=begin + relativedelta(months=j)
                            sign=0
                            for k in order:
                                start=k.start_time
                                end=k.end_time
                                if start<=day<=end:  
                                    sign=1
                                    break
                            if sign==1:
                                s+='1'    
                            else:
                                s+='0' 
                    else:
                        s="000000000000000000000000000000"    
                d["s"] = s            
                house.append(d)
            result["house"] = house
            return JsonResponse(result)
        result = {'result': 1, 'message': '获取成功!'}
        user=UserInfo.objects.get(userID=id)
        all = RHouse.objects.filter(status="正常出售")
        house = []
        for i in all:
            d = {}
            d["HouseID"] = i.HouseID
            d["price"] = i.price
            d["name"] = i.name
            d["type"] = i.type
            d["style"] = i.style
            d["address"] = i.address
            d["house_size"] = i.house_size
            d["category"] = i.category
            d["is_near_subway"] = i.is_near_subway
            d["is_has_dw"] = i.is_has_dw
            d["is_has_yt"] = i.is_has_yt
            d["total_views"] = i.total_views
            if RCollect.objects.filter(userID=id, HouseID=i.HouseID).exists() == True:
                d["is_collect"]=1
            else:
                d["is_collect"]=0
            if RImg.objects.filter(HouseID=i.HouseID).exists() == True:
                imgs = RImg.objects.filter(HouseID=i.HouseID)
                d["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url                                 
            else:
                d["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"
            if(type==1):
                begin = date.today()
                end=begin + timedelta(days=30)
                exist = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3).first()
                s=""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3)
                    for j in range((end - begin).days+1):
                        day = begin + datetime.timedelta(days=j)
                        sign=0
                        for k in order:
                            start=k.start_time
                            end=k.end_time
                            if start<=day<=end:  
                                sign=1
                                break
                        if sign==1:
                            s+='1'    
                        else:
                            s+='0'                            
                else:
                    s="000000000000000000000000000000"           
            else:
                begin = date.today()
                end=begin + relativedelta(months=12)
                exist = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3).first()
                s=""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3)
                    for j in range(0,12):
                        day=begin + relativedelta(months=j)
                        sign=0
                        for k in order:
                            start=k.start_time
                            end=k.end_time
                            if start<=day<=end:  
                                sign=1
                                break
                        if sign==1:
                            s+='1'    
                        else:
                            s+='0' 
                else:
                    s="000000000000000000000000000000"    
            d["s"] = s            
            house.append(d)
        result["house"] = house
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def house_list_U(request):  # 查询所有房间
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        order= Order.objects.filter(userID=id,OrderState=4)
        a=datetime.date.today()
        list=[]
        result = {'result': 1, 'message': '查询成功！'}
        for j in order:
            i= RHouse.objects.get(HouseID=j.HouseID)
            
            end=a + timedelta(days=2)
            if( not (a<=j.end_time and a>=j.start_time)):
                continue
            
            d = {'HouseID': i.HouseID, 'name': i.name, 'type': i.type, 'price': i.price, 'address':i.address, 'house_size': i.house_size, 'status': i.status,
                 'category': i.category, 'is_near_subway': i.is_near_subway, 'is_has_dw': i.is_has_dw, 'is_has_yt': i.is_has_yt, 'total_views': i.total_views,'style':i.style,'summary':i.summary,'rules':i.rules,'bed':i.bed,'type':i.type,'end_time':j.end_time,'OrderID':j.OrderID}

            if(i.type =="长租"):          
                day=j.start_time + relativedelta(months=(j.cnt+1))           
                if (a-j.start_time).days>=0 and (j.end_time-a).days>=0 and (day-a).days<=7:
                    d["near"]=1
                else:
                    d["near"]=0
                if((a-j.start_time).days>=0 and  (a-day).days>=0):
                    d["overtime"]=1
                else:
                    d["overtime"]=0
                day1=j.start_time + relativedelta(months=(j.cnt))
                day2=j.start_time + relativedelta(months=(j.cnt+1))
                if (a-day1).days>=0 and (day2-a).days>=0:
                    d['paid']=0
                else:
                    d['paid']=1

                
            if RImg.objects.filter(HouseID=i.HouseID).exists() == True:
                imgs = RImg.objects.filter(HouseID=i.HouseID)
                d["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url    
                                    
            else:
                d["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"
            if(type==1):
                begin = date.today()
                end=begin + timedelta(days=30)
                exist = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3).first()
                s=""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3)
                    for j in range((end - begin).days+1):
                        day = begin + datetime.timedelta(days=j)
                        sign=0
                        for k in order:
                            start=k.start_time
                            end=k.end_time
                            if start<=day<=end:  
                                sign=1
                                break
                        if sign==1:
                            s+='1'    
                        else:
                            s+='0'                            
                else:
                    s="000000000000000000000000000000"           
            else:
                begin = date.today()
                end=begin + relativedelta(months=12)
                exist = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3).first()
                s=""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3)
                    for j in range(0,12):
                        day=begin + relativedelta(months=j)
                        sign=0
                        for k in order:
                            start=k.start_time
                            end=k.end_time
                            if start<=day<=end:  
                                sign=1
                                break
                        if sign==1:
                            s+='1'    
                        else:
                            s+='0' 
                else:
                    s="000000000000000000000000000000"    
            d["s"] = s
            list.append(d)
        result['len'] = len(list)
        result['list'] = list
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def recommend(request):  # 查询所有房间
    if request.method == 'POST':
        House= RHouse.objects.filter(status="正常出售").order_by('-total_views')
        list=[]
        result = {'result': 1, 'message': '查询成功！'}
        for i in House[:4]:       
            d = {'HouseID': i.HouseID, 'name': i.name, 'type': i.type, 'price': i.price, 'address':i.address, 'house_size': i.house_size, 'status': i.status,
                 'category': i.category, 'is_near_subway': i.is_near_subway, 'is_has_dw': i.is_has_dw, 'is_has_yt': i.is_has_yt, 'total_views': i.total_views,'style':i.style,'summary':i.summary,'rules':i.rules,'bed':i.bed,'type':i.type}

            if RImg.objects.filter(HouseID=i.HouseID).exists() == True:
                imgs = RImg.objects.filter(HouseID=i.HouseID)
                d["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url    
                                             
            else:
                d["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"
            if(i.type=="短租"):
                begin = date.today()
                end=begin + timedelta(days=30)
                exist = Order.objects.filter(HouseID=i.HouseID).first()
                s=""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID)
                    for j in range((end - begin).days+1):
                        day = begin + datetime.timedelta(days=j)
                        sign=0
                        for k in order:
                            start=k.start_time
                            end=k.end_time
                            if start<=day<=end:  
                                sign=1
                                break
                        if sign==1:
                            s+='1'    
                        else:
                            s+='0'                            
                else:
                    s="000000000000000000000000000000"           
            else:
                begin = date.today()
                end=begin + relativedelta(months=12)
                exist = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3).first()
                s=""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3)
                    for j in range(0,12):
                        day=begin + relativedelta(months=j)
                        sign=0
                        for k in order:
                            start=k.start_time
                            end=k.end_time
                            if start<=day<=end:  
                                sign=1
                                break
                        if sign==1:
                            s+='1'    
                        else:
                            s+='0' 
                else:
                    s="000000000000000000000000000000"    
            d["s"] = s
            list.append(d)
        result['len'] = len(list)
        result['list'] = list
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def search(request):
    if request.method == 'POST':
        token = request.META.get('HTTP_AUTHORIZATION', 0)
        id = Check(token)
        result = {'result': 1, 'message': '搜索成功!'}
        data_json = json.loads(request.body)
        type = data_json.get('type')
        key = str(data_json.get('key'))
        category = data_json.get('category')
        start_time = data_json.get('start_time')
        end_time = data_json.get('end_time')
        address = data_json.get('address')
        if start_time!= '':
            start_time = datetime.datetime.date(datetime.datetime.strptime(start_time,"%Y-%m-%d"))
        if end_time!= '':
            end_time = datetime.datetime.date(datetime.datetime.strptime(end_time,"%Y-%m-%d"))
        object = []
        good = RHouse.objects.filter(name__icontains=key)
        for i in good:
            if (category!='' and i.category != category) or (type!='' and i.type != type) or (address not in i.address) or (key not in i.name):
                continue
            d = {'HouseID': i.HouseID, 'name': i.name, 'type': i.type, 'price': i.price, 'address': i.address, 'house_size': i.house_size, 'status': i.status,
                 'category': i.category, 'is_near_subway': i.is_near_subway, 'is_has_dw': i.is_has_dw, 'is_has_yt': i.is_has_yt, 'total_views': i.total_views, 'style': i.style, 'summary': i.summary, 'rules': i.rules, 'bed': i.bed}
            if RImg.objects.filter(HouseID=i.HouseID).exists() == True:
                imgs = RImg.objects.filter(HouseID=i.HouseID)
                d["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url    
                                          
            else:
                d["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"

            if(id==-1):
                d["is_collect"]=0
            else:
                if RCollect.objects.filter(userID=id, HouseID=i.HouseID).exists() :
                    d["is_collect"]=1
                else:
                    d["is_collect"]=0
     
            if i.type == '短租':
                begin = datetime.date.today()
                end = begin + datetime.timedelta(days=30)
                exist = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3).first()
                s = ""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3)
                    for j in range((end - begin).days+1):
                        day = begin + datetime.timedelta(days=j)
                        sign = 0
                        for k in order:
                            start = k.start_time
                            end = k.end_time
                            if start <= day <= end:
                                sign = 1
                                break
                        if sign == 1:
                            s += '1'
                        else:
                            s += '0'
                else:
                    s = "000000000000000000000000000000"
                if start_time!='' and start_time!=None:
                    start_index = (start_time-begin).days
                    end_index = (end_time-begin).days
                    isable = True
                    for j in range(start_index, end_index):
                        if s[j] == '1':
                            isable = False
                            break
                    if not isable:
                        continue
            elif type=='长租':
                begin = datetime.date.today()
                end = begin + relativedelta(months=12)
                exist = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3).first()
                s = ""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3)
                    for j in range(0, 12):
                        day = begin + relativedelta(months=j)
                        sign = 0
                        for k in order:
                            start = k.start_time
                            end = k.end_time
                            if start <= day <= end:
                                sign = 1
                                break
                        if sign == 1:
                            s += '1'
                        else:
                            s += '0'
                else:
                    s = "000000000000"
                if start_time!='' and start_time!=None:
                    start_index = (start_time.month-begin.month)
                    end_index = (end_time.month-begin.month)
                    isable = True
                    for j in range(start_index, end_index):
                        if s[j] == '1':
                            isable = False
                            break
                    if not isable:
                        continue
            object.append(d)

        # Search object by given id
        result['len'] = len(object)
        result['object'] = object
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def house_collect(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        HouseID = int(data_json.get('HouseID'))
        if RCollect.objects.filter(userID=id, HouseID=HouseID).exists() == True:
            result = {'result': 0, 'message': '已收藏该商品!'}
            return JsonResponse(result)
        RCollect.objects.create(userID=id, HouseID=HouseID)
        result = {'result': 1, 'message': '收藏成功!'}
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def house_uncollect(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')

        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        HouseID = int(data_json.get('HouseID'))
        if RCollect.objects.filter(userID=id, HouseID=HouseID).exists() == False:
            result = {'result': 0, 'message': '未收藏该商品!'}
            return JsonResponse(result)
        Collect = RCollect.objects.get(userID=id, HouseID=HouseID)
        Collect.delete()
        result = {'result': 1, 'message': '取消收藏成功!'}
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def collect_list(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')      
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        collect=RCollect.objects.filter(userID=id)
        list=[]
        result = {'result': 1, 'message': '查询成功！'}
        for i in collect:
            House=RHouse.objects.get(HouseID=i.HouseID)
            d = {'HouseID': House.HouseID, 'name': House.name, 'type': House.type, 'price': House.price, 'address': House.address, 'house_size': House.house_size, 'status': House.status,
                 'category': House.category, 'is_near_subway': House.is_near_subway, 'is_has_dw': House.is_has_dw, 'is_has_yt': House.is_has_yt, 'total_views': House.total_views,'style':House.style,'summary':House.summary,'rules':House.rules,'bed':House.bed,'type':House.type}
            if RImg.objects.filter(HouseID=i.HouseID).exists() == True:
                imgs = RImg.objects.filter(HouseID=i.HouseID)
                d["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url    
                                            
            else:
                d["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"
            if(House.type=="短租"):
                begin = date.today()
                end=begin + timedelta(days=30)
                exist = Order.objects.filter(HouseID=i.HouseID,OrderState=4).first()
                s=""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID,OrderState=4)
                    for j in range((end - begin).days+1):
                        day = begin + datetime.timedelta(days=j)
                        sign=0
                        for k in order:
                            start=k.start_time
                            end=k.end_time
                            if start<=day<=end:  
                                sign=1
                                break
                        if sign==1:
                            s+='1'    
                        else:
                            s+='0'                            
                else:
                    s="000000000000000000000000000000"           
            else:
                begin = date.today()
                end=begin + relativedelta(months=12)
                exist = Order.objects.filter(HouseID=i.HouseID,OrderState=4).first()
                s=""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID,OrderState=4)
                    for j in range(0,12):
                        day=begin + relativedelta(months=j)
                        sign=0
                        for k in order:
                            start=k.start_time
                            end=k.end_time
                            if start<=day<=end:  
                                sign=1
                                break
                        if sign==1:
                            s+='1'    
                        else:
                            s+='0' 
                else:
                    s="000000000000000000000000000000"    
            d["s"] = s
            list.append(d)
        result['len'] = len(list)
        result['list'] = list
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)



@csrf_exempt
def room_update(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        HouseID = int(data_json.get('HouseID'))
        newhouse = RHouse.objects.get(HouseID=HouseID)
        newhouse.name = data_json.get('title')
        newhouse.description = data_json.get('description')
        newhouse.category = data_json.get('category')
        newhouse.price = int(data_json.get('price'))
        newhouse.address = data_json.get('address')
        newhouse.house_size = int(data_json.get('house_size'))
        newhouse.is_near_subway = int(data_json.get('is_near_subway'))
        newhouse.is_has_dw = int(data_json.get('is_has_dw'))
        newhouse.is_has_yt = int(data_json.get('is_has_yt'))
        newhouse.total_views = int(data_json.get('total_views'))
        newhouse.style= data_json.get('style')  
        newhouse.summary= data_json.get('summary')
        newhouse.rules= data_json.get('rules')
        newhouse.bed=int(data_json.get('bed'))
        newhouse.status=data_json.get('status')
        newhouse.save()
        result = {'result': 1, 'message': '修改成功!', 'id': newhouse.HouseID}
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def roominfo(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = request.META.get('HTTP_AUTHORIZATION', 0)
        id = Check(token)
        HouseID = int(data_json.get('HouseID'))

        result = {}
        House = RHouse.objects.get(HouseID=HouseID)
        House.total_views=House.total_views+1
        House.save()
        if(token==None):
            result['iscollect']=False
        else:
            if RCollect.objects.filter(userID=id, HouseID=House.HouseID).exists():
                result['iscollect'] = True
            else:
                result['iscollect'] = False
        result['userID'] = id
        result["title"] = House.name
        result["price"] = House.price
        result["address"] = House.address
        result["house_size"] = House.house_size
        result["status"] = House.status
        result["category"] = House.category
        result["type"] = House.type
        result["is_near_subway"] = House.is_near_subway
        result["is_has_dw"] = House.is_has_dw
        result["is_has_yt"] = House.is_has_yt
        result["total_views"] = House.total_views
        result["style"] = House.style
        result["summary"] = House.summary
        result["rules"] = House.rules
        result["bed"] = House.bed
        if(House.type=="短租"):
            begin = date.today()
            end=begin + timedelta(days=30)
            exist = Order.objects.filter(HouseID=House.HouseID).exclude(OrderState=3).first()
            s=""
            if exist:
                order = Order.objects.filter(HouseID=House.HouseID).exclude(OrderState=3)
                for j in range((end - begin).days+1):
                    day = begin + datetime.timedelta(days=j)
                    sign=0
                    for k in order:
                        start=k.start_time
                        end=k.end_time
                        if start<=day<=end:  
                            sign=1
                            break
                    if sign==1:
                        s+='1'    
                    else:
                        s+='0'                            
            else:
                s="000000000000000000000000000000"           
        else:
            begin = date.today()
            end=begin + relativedelta(months=12)
            exist = Order.objects.filter(HouseID=House.HouseID).exclude(OrderState=3).first()
            s=""
            if exist:
                order = Order.objects.filter(HouseID=House.HouseID).exclude(OrderState=3)
                for j in range(0,12):
                    day=begin + relativedelta(months=j)
                    sign=0
                    for k in order:
                        start=k.start_time
                        end=k.end_time
                        if start<=day<=end:  
                            sign=1
                            break
                    if sign==1:
                        s+='1'    
                    else:
                        s+='0' 
            else:
                s="0000000000000000000"    
        result["s"] = s
        if RImg.objects.filter(HouseID=HouseID).exists():
            imgs = RImg.objects.filter(HouseID=HouseID)
            result["images"] = [{'url':'http://43.138.77.8/dz/roomhubSite'+i.img.url,'imgid':i.imgid} for i in imgs]
        else:
            result["images"] = [{'url':"https://z3.ax1x.com/2021/06/09/2cqBCD.png",'imgid':-1}]

        result["result"] = 1
        result["message"] = "查询成功"
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def charge(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': '请先登录!'}
            return JsonResponse(result)
        else:
            money = int(data_json.get('money'))
            user=UserInfo.objects.get(id)
            user.money=user.money+money
            user.save()
            result = {'result': 1, 'message': '充值成功!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def apply(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': '请先登录!'}
            return JsonResponse(result)
        else:
            OrderID = int(data_json.get('OrderID'))
            user=UserInfo.objects.get(userID=id)
            if Order.objects.filter(OrderID=OrderID).exists() == True:
                order=Order.objects.get(OrderID=OrderID)
                House=RHouse.objects.get(HouseID=order.HouseID)
                if(order.OrderState==1):
                    result = {'result': 0, 'message': '待审核'}
                    return JsonResponse(result)
                if(order.OrderState==3):
                    result = {'result': 0, 'message': '未通过审核'}
                    return JsonResponse(result)
                if(order.OrderState==4):
                    result = {'result': 0, 'message': '不能重复支付'}
                    return JsonResponse(result)
                if(House.price<=user.money):
                    user.money=user.money-House.price
                    user.save()
                    order.OrderState=4
                    order.save()
                    result = {'result': 1, 'message': '购买成功!'}
                    return JsonResponse(result)
                else:
                    result = {'result': 0, 'message': '余额不足!'}
                    return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '订单不存在!'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def humancheck(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': '请先登录!'}
            return JsonResponse(result)
        else:
            user=UserInfo.objects.get(userID=id)
            reason = data_json.get('reason')
            if user.role!=1:
                result = {'result': 0, 'message': '没有权限!'}
                return JsonResponse(result)
            else:
                judge = data_json.get('judge')
                OrderID = data_json.get('OrderID')
                order=Order.objects.get(OrderID=OrderID)
                order.reason=reason
                order.save()
                if judge:
                    order.OrderState=2
                    order.save()
                    if RHouse.objects.get(HouseID=order.HouseID).type=='短租':
                        result = {'result': 1, 'message': '审核通过!','reason':reason}
                        return JsonResponse(result)
                    order.OrderState=5
                    order.save()
                    story = []
                    title_style = ParagraphStyle(name="TitleStyle", fontName="msyh", fontSize=10, alignment=TA_CENTER, )
                    content_style = ParagraphStyle(name="ContentStyle",
                                                fontName="msyh",
                                                fontSize=7,
                                                alignment=TA_LEFT, )
                    content_style_1 = ParagraphStyle(name="ContentStyle",
                                                    fontName="msyh",
                                                    fontSize=9,
                                                    leftIndent=20,
                                                    alignment=TA_LEFT, )
                    content_style_line = ParagraphStyle(name="ContentStyle",
                                                        fontName="msyh",
                                                        fontSize=9,
                                                        underlineOffset=-3,
                                                        alignment=TA_LEFT, )
                    content_style_line_1 = ParagraphStyle(name="ContentStyle",
                                                        fontName="msyh",
                                                        fontSize=7,
                                                        underlineOffset=-3,
                                                        alignment=TA_LEFT, )
                    task_data = [['房间名称', '开始时间', '结束时间'],
                                [order.Hname, order.start_time,order.end_time],
                                ]
                    basic_style = TableStyle([('FONTNAME', (0, 0), (-1, -1), 'msyh'),
                                            ('FONTSIZE', (0, 0), (-1, -1), 7),
                                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                                            # 'SPAN' (列,行)坐标
                                            ('SPAN', (1, 0), (2, 0)),
                                            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                            ])
                    story.append(Spacer(1, 10 * mm))
                    story.append(Paragraph("合同", title_style))
                    story.append(Spacer(1, 5 * mm))
                    story.append(Paragraph("单位名称： 青年租房管理系统", content_style))
                    story.append(Spacer(1, 2 * mm))
                    story.append(Paragraph("订单编号： <u> {} </u>".format(order.OrderID), content_style))
                    story.append(Spacer(1, 2 * mm))
                    story.append(
                        Paragraph("<u>租客可于当晚前往青年租房管理系统官网（http://43.138.77.8/dz/roomhubSite/） 查询详细的凭证信息。</u>",
                                content_style_line))
                    story.append(Spacer(1, 2 * mm, isGlue=True))
                    story.append(
                        Paragraph("租客姓名:"+ order.name+"&nbsp&nbsp&nbsp" +"证件类型：居民身份证 &nbsp&nbsp&nbsp 证件号码："+ order.CardID, content_style))
                    story.append(Paragraph("租客电话：" +order.telephone+"&nbsp&nbsp&nbsp" +"租客邮箱"+order.Email, content_style))
                    story.append(Paragraph("保险期间：自北京时间起  "+str(order.start_time)+" 至  "+str(order.end_time)+" 时止", content_style))
                    story.append(Paragraph("支付时间：  "+str(order.OrderDate)+" 约定到账周期： 3 天  支付方式： 银行汇款", content_style))
                    task_table = Table(task_data, colWidths=[75 * mm, 50 * mm, 40 * mm], rowHeights=8 * mm, style=basic_style)
                    story.append(task_table)
                    story.append(Paragraph("总金额： &nbsp&nbsp "+str(order.price)+" 元", content_style))
                    story.append(Paragraph("条款适用： 青年租房管理系统《非金融机构支付服务保险条款》", content_style_line_1))
                    story.append(Paragraph(
                        "<u>_____________________________________________________________________________________________________________________________________________________</u>",
                        content_style_line_1))
                    story.append(Paragraph("特别约定：", content_style))
                    for item in rule:
                        story.append(Paragraph(item, content_style))
                    story.append(Paragraph(
                        "<u>_____________________________________________________________________________________________________________________________________________________</u>",
                        content_style_line_1))
                    story.append(Paragraph('合同争议解决方式： 诉讼 付款方式：趸缴', content_style))
                    doc = SimpleDocTemplate(str(order.OrderID)+".pdf",
                                            leftMargin=20 * mm, rightMargin=20 * mm, topMargin=2 * mm, bottomMargin=20 * mm)
                    doc.build(story)
                    RContract.objects.create(start_time=order.start_time, end_time=order.end_time, price=order.price,userID=order.userID,Email=order.Email,OrderDate=order.OrderDate,HouseID=order.HouseID,CardID=order.CardID,name=order.name,Hname=order.Hname,telephone=order.telephone,OrderID=order.OrderID)
                    result = {'result': 1, 'message': '审核通过!','reason':reason}
                    SendSEmail(order.Email)
                else:
                    order.OrderState=3
                    order.save()
                    result = {'result': 1, 'message': '审核不通过!','reason':reason}
                    SendFEmail(Order.Email)
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def generate_order(request): 
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        if(token==None):
            result = {'result': 0, 'message': '请先登录!'}
            return JsonResponse(result)
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            HouseID = int(data_json.get('HouseID'))
            if RHouse.objects.filter(HouseID=HouseID).exists() == True:
                House = RHouse.objects.get(HouseID=HouseID)
                if House.status == 2:
                    result = {'result': 0, 'message': '房间已租'}
                    return JsonResponse(result)
                elif House.status == 3:
                    result = {'result': 0, 'message': '房间暂停出售'}
                else:
                    start_time = data_json.get('start_time')
                    end_time = data_json.get('end_time')
                    price = int(data_json.get('price'))
                    HouseID=int(data_json.get('HouseID'))
                    idcard=data_json.get('CardID')
                    name=data_json.get('name')
                    House = RHouse.objects.get(HouseID=HouseID)
                    user = UserInfo.objects.get(userID=id)
                    email = user.email
                    Hname=House.name
                    telephone=data_json.get('telephone')

                    order=Order.objects.create(start_time=start_time, end_time=end_time, price=price, name=name, userID=id,Email=email,Hname=Hname,CardID=idcard,telephone=telephone,OrderState=1,see=1,HouseID=HouseID)
                    Errors=['验证通过!','身份证号码位数不对!','身份证号码出生日期超出范围或含有非法字符!','身份证号码校验错误!','身份证地区非法!']
                    area={"11":"北京","12":"天津","13":"河北","14":"山西","15":"内蒙古","21":"辽宁","22":"吉林","23":"黑龙江","31":"上海","32":"江苏","33":"浙江","34":"安徽","35":"福建","36":"江西","37":"山东","41":"河南","42":"湖北","43":"湖南","44":"广东","45":"广西","46":"海南","50":"重庆","51":"四川","52":"贵州","53":"云南","54":"西藏","61":"陕西","62":"甘肃","63":"青海","64":"宁夏","65":"新疆","71":"台湾","81":"香港","82":"澳门","91":"国外"}
                    idcard=str(idcard)
                    idcard=idcard.strip()
                    idcard_list=list(idcard)
                    #地区校验
                    if((idcard)[0:2] not in area) or (not area[(idcard)[0:2]]):
                        result = {'result': 0, 'message':Errors[4]}
                        order.OrderState=3
                        order.save()
                        return JsonResponse(result)
                    #15位身份号码检测
                    if(len(idcard)==15):
                        if((int(idcard[6:8])+1900) % 4 == 0 or((int(idcard[6:8])+1900) % 100 == 0 and (int(idcard[6:8])+1900) % 4 == 0 )):
                            erg=re.compile('[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}$')#//测试出生日期的合法性
                        else:
                            ereg=re.compile('[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}$')#//测试出生日期的合法性
                        if(not re.match(ereg,idcard)):
                            result = {'result': 0, 'message':Errors[2]}
                            order.OrderState=3
                            order.save()
                            return JsonResponse(result)
                    #18位身份号码检测
                    elif(len(idcard)==18):
                        #出生日期的合法性检查
                        #闰年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))
                        #平年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))
                        if(int(idcard[6:10]) % 4 == 0 or (int(idcard[6:10]) % 100 == 0 and int(idcard[6:10])%4 == 0 )):
                            ereg=re.compile('[1-9][0-9]{5}(19[0-9]{2}|20[0-9]{2})((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}[0-9Xx]$')#//闰年出生日期的合法性正则表达式
                        else:
                            ereg=re.compile('[1-9][0-9]{5}(19[0-9]{2}|20[0-9]{2})((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}[0-9Xx]$')#//平年出生日期的合法性正则表达式
                        #//测试出生日期的合法性
                        if(re.match(ereg,idcard)):
                            #//计算校验位
                            S = (int(idcard_list[0]) + int(idcard_list[10])) * 7 + (int(idcard_list[1]) + int(idcard_list[11])) * 9 + (int(idcard_list[2]) + int(idcard_list[12])) * 10 + (int(idcard_list[3]) + int(idcard_list[13])) * 5 + (int(idcard_list[4]) + int(idcard_list[14])) * 8 + (int(idcard_list[5]) + int(idcard_list[15])) * 4 + (int(idcard_list[6]) + int(idcard_list[16])) * 2 + int(idcard_list[7]) * 1 + int(idcard_list[8]) * 6 + int(idcard_list[9]) * 3
                            Y = S % 11
                            M = "F"
                            JYM = "10X98765432"
                            M = JYM[Y]#判断校验位
                            if(M != idcard_list[17]):#检测ID的校验位
                                result = {'result': 0, 'message':Errors[3]}
                                order.OrderState=3
                                order.save()
                                return JsonResponse(result)
                        else:
                            result = {'result': 0, 'message':Errors[2]}
                            order.OrderState=3
                            order.save()
                            return JsonResponse(result)
                    else:
                        result = {'result': 0, 'message':Errors[1]}
                        order.OrderState=3
                        order.save()
                        return JsonResponse(result)
                    pattern = re.compile(r'^(13[0-9]|14[0|5|6|7|9]|15[0|1|2|3|5|6|7|8|9]|'
                         r'16[2|5|6|7]|17[0|1|2|3|5|6|7|8]|18[0-9]|'
                         r'19[1|3|5|6|7|8|9])\d{8}$')
                    if not pattern.search(telephone):
                        result = {'result': 0, 'message':'手机号码非法！'}
                        order.OrderState=3
                        order.save()
                        return JsonResponse(result)
                    result = {'result': 1, 'message':'第一次审核通过'}
                    return JsonResponse(result)    
            else:
                result = {'result': 0, 'message': '房间不存在'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def orderlist(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        Orders=Order.objects.filter(userID=id,see=1)
        list=[]
        result = {'result': 1, 'message': '查询成功！'}
        for i in Orders:
            House=RHouse.objects.get(HouseID=i.HouseID)
            d = {'OrderID': i.OrderID, 'OrderState': i.OrderState, 'HouseID': i.HouseID, 'userID': i.userID, 'OrderDate': i.OrderDate, 'Email': i.Email, 'CardID': i.CardID,
                 'name': i.name, 'Hname': i.Hname, 'telephone': i.telephone, 'start_time': i.start_time, 'end_time': i.end_time,'price':i.price,'see':i.see,'address':House.address,'single_price':House.price,'house_size':House.house_size,'status':House.status,'category':House.category,'type':House.type,'is_near_subway':House.is_near_subway,'is_has_dw':House.is_has_dw,'is_has_yt':House.is_has_yt,'total_views':House.total_views,'style':House.style,'summary':House.summary,'rules':House.rules,'bed':House.bed}
            if RImg.objects.filter(HouseID=i.HouseID).exists() :
                imgs = RImg.objects.filter(HouseID=i.HouseID)
                d["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url    
            else:
                d["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"
            list.append(d)
        result['len'] = len(list)
        result['list'] = list
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def orderinfo(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)

        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:

            OrderID = int(data_json.get('OrderID'))
            result = {}
            content = Order.objects.get(OrderID=OrderID)
            House=RHouse.objects.get(HouseID=content.HouseID)
            if Order.objects.filter(OrderID=OrderID).exists():
                content = Order.objects.get(OrderID=OrderID)
                result["start_time"] = content.start_time
                result["end_time"] = content.end_time
                result["price"] = content.price
                result["email"]= content.Email
                result["HouseID"]=content.HouseID
                result["CardID"]=content.CardID
                result["name"]=content.name
                result["Hname"]=content.Hname
                result["telephone"]=content.telephone
                result["OrderState"]=content.OrderState
                result["OrderDate"]=content.OrderDate
                result["userID"]=content.userID
                result["OrderID"]=content.OrderID
                result["see"]=content.see
                result["address"]=House.address
                result["signle_price"]=House.price
                result["house_size"]=House.house_size
                result["status"]=House.status
                result["category"]=House.category
                result["type"]=House.type
                result["is_near_subway"]=House.is_near_subway
                result["is_has_dw"]=House.is_has_dw
                result["is_has_yt"]=House.is_has_yt
                result["total_views"]=House.total_views
                result["style"]=House.style
                result["reason"]=content.reason
                result["summary"]=House.summary
                result["rules"]=House.rules
                result["bed"]=House.bed
                result["result"] = 1
                result["message"] = "查询成功"
                if RImg.objects.filter(HouseID=content.HouseID).exists() :
                    imgs = RImg.objects.filter(HouseID=content.HouseID)
                    result["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url    
                else:
                    result["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '订单不存在'}
                return JsonResponse(result)

    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def order_delete(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)

        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            OrderID = int(data_json.get('OrderID'))
            if Order.objects.filter(OrderID=OrderID).exists():
                content = Order.objects.get(OrderID=OrderID)
                content.see=2
                content.save()
                result = {'result': 1, 'message': '删除成功'}
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '订单不存在'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def extension(request):    #长租续约
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            OrderID = int(data_json.get('OrderID'))
            month=int(data_json.get('month'))
            if Order.objects.filter(OrderID=OrderID).exists():
                content = Order.objects.get(OrderID=OrderID)
                start_time = data_json.get('start_time')
                end_time = data_json.get('end_time')
                price = int(data_json.get('price'))
                House = RHouse.objects.get(HouseID=content.HouseID)
                user = UserInfo.objects.get(userID=id)
                email = user.email
                Hname=House.name
                order=Order.objects.create(start_time=start_time, end_time=end_time, price=price, name=content.name, userID=id,Email=user.email,Hname=Hname,CardID=content.CardID,telephone=content.telephone,OrderState=5,see=1,HouseID=content.HouseID)
                story = []
                title_style = ParagraphStyle(name="TitleStyle", fontName="msyh", fontSize=10, alignment=TA_CENTER, )
                content_style = ParagraphStyle(name="ContentStyle",
                                            fontName="msyh",
                                            fontSize=7,
                                            alignment=TA_LEFT, )
                content_style_1 = ParagraphStyle(name="ContentStyle",
                                                fontName="msyh",
                                                fontSize=9,
                                                leftIndent=20,
                                                alignment=TA_LEFT, )
                content_style_line = ParagraphStyle(name="ContentStyle",
                                                    fontName="msyh",
                                                    fontSize=9,
                                                    underlineOffset=-3,
                                                    alignment=TA_LEFT, )
                content_style_line_1 = ParagraphStyle(name="ContentStyle",
                                                    fontName="msyh",
                                                    fontSize=7,
                                                    underlineOffset=-3,
                                                    alignment=TA_LEFT, )
                task_data = [['房间名称', '开始时间', '结束时间'],
                            [order.Hname, order.start_time,order.end_time],
                            ]
                basic_style = TableStyle([('FONTNAME', (0, 0), (-1, -1), 'msyh'),
                                        ('FONTSIZE', (0, 0), (-1, -1), 7),
                                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                                        # 'SPAN' (列,行)坐标
                                        ('SPAN', (1, 0), (2, 0)),
                                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                        ])
                story.append(Spacer(1, 10 * mm))
                story.append(Paragraph("合同", title_style))
                story.append(Spacer(1, 5 * mm))
                story.append(Paragraph("单位名称： 青年租房管理系统", content_style))
                story.append(Spacer(1, 2 * mm))
                story.append(Paragraph("订单编号： <u> {} </u>".format(order.OrderID), content_style))
                story.append(Spacer(1, 2 * mm))
                story.append(
                    Paragraph("<u>租客可于当晚前往青年租房管理系统官网（http://43.138.77.8/dz/roomhubSite/） 查询详细的凭证信息。</u>",
                            content_style_line))
                story.append(Spacer(1, 2 * mm, isGlue=True))
                story.append(
                    Paragraph("租客姓名:"+ order.name+"&nbsp&nbsp&nbsp" +"证件类型：居民身份证 &nbsp&nbsp&nbsp 证件号码："+ order.CardID, content_style))
                story.append(Paragraph("租客电话：" +order.telephone+"&nbsp&nbsp&nbsp" +"租客邮箱"+order.Email, content_style))
                story.append(Paragraph("保险期间：自北京时间起  "+str(order.start_time)+" 至  "+str(order.end_time)+" 时止", content_style))
                story.append(Paragraph("支付时间：  "+str(order.OrderDate)+" 约定到账周期： 3 天  支付方式： 银行汇款", content_style))
                task_table = Table(task_data, colWidths=[75 * mm, 50 * mm, 40 * mm], rowHeights=8 * mm, style=basic_style)
                story.append(task_table)
                story.append(Paragraph("总金额： &nbsp&nbsp "+str(order.price)+" 元", content_style))
                story.append(Paragraph("条款适用： 青年租房管理系统《非金融机构支付服务保险条款》", content_style_line_1))
                story.append(Paragraph(
                    "<u>_____________________________________________________________________________________________________________________________________________________</u>",
                    content_style_line_1))
                story.append(Paragraph("特别约定：", content_style))
                for item in rule:
                    story.append(Paragraph(item, content_style))
                story.append(Paragraph(
                    "<u>_____________________________________________________________________________________________________________________________________________________</u>",
                    content_style_line_1))
                story.append(Paragraph('合同争议解决方式： 诉讼 付款方式：趸缴', content_style))
                doc = SimpleDocTemplate(str(order.OrderID)+".pdf",
                                        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=2 * mm, bottomMargin=20 * mm)
                doc.build(story)
                RContract.objects.create(start_time=order.start_time, end_time=order.end_time, price=order.price,userID=order.userID,Email=order.Email,OrderDate=order.OrderDate,HouseID=order.HouseID,CardID=order.CardID,name=order.name,Hname=order.Hname,telephone=order.telephone,OrderID=order.OrderID)
                result = {'result': 1, 'message': '续租成功'}
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '订单不存在'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def uploadinfo_M(request):  # 客服修改用户基础信息
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user=UserInfo.objects.get(userID=id)
        if(user.role!=1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result)
        userID = int(data_json.get('userID'))
        if UserInfo.objects.filter(userID=userID).exists():
            user = UserInfo.objects.get(userID=userID)
            user.sex = int(data_json.get('sex'))
            user.telephone= data_json.get('telephone')
            user.username= data_json.get('username')
            email= data_json.get('email')
            user.birth= data_json.get('birth')
            user.CardID= data_json.get('CardID')
            user.summary= data_json.get('summary')
            if email==user.email:
                user.email= data_json.get('email')
                user.save()
                result = {'result': 1, 'message': '修改成功!'}
                return JsonResponse(result)
            if UserInfo.objects.filter(email=email).exists():
                result = {'result': 0, 'message': '邮箱已注册!'}
                return JsonResponse(result)
            else:
                user.email= data_json.get('email')
                user.save()
                result = {'result': 1, 'message': '修改成功!'}
                return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '用户不存在!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def user_info(request):  # 查看租客详情
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user=UserInfo.objects.get(userID=id)
        if(user.role!=1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result)
        userID = data_json.get('userID')
        if UserInfo.objects.filter(userID=userID).exists():
            user=UserInfo.objects.get(userID=userID)
            result={'result': 1, 'message': '查询成功!', 'username': user.username, 'userID': user.userID,
                  'url':user.get_photo_url, 'email': user.email, 'role': user.role,'money':user.money,'age':user.age,'sex':user.sex,'telephone':user.telephone,'birth':user.birth,'summary':user.summary,'CardID':user.CardID}
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '用户不存在!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def user_list(request):  # 查看租客列表
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user=UserInfo.objects.get(userID=id)
        if(user.role!=1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result)
        users=UserInfo.objects.filter(role=2)
        list=[]
        result = {'result': 1, 'message': '查询成功！'}
        for i in users:
            d = {'username': i.username, 'userID': i.userID,'url': i.get_photo_url, 'email': i.email, 'role': i.role,'money':i.money,'age':i.age,'sex':i.sex,'telephone':i.telephone,'birth':i.birth,'CardID':i.CardID}
            list.append(d)
        result['len'] = len(list)
        result['list'] = list
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def contract_list_M(request):  # 查看合同列表
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user=UserInfo.objects.get(userID=id)
        if(user.role!=1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result) 
        contracts=RContract.objects.all()
        list=[]
        result = {'result': 1, 'message': '查询成功！'}
        for i in contracts:
            House=RHouse.objects.get(HouseID=i.HouseID)
            d = {'ContractID':i.ContractID,'start_time':i.start_time, 'end_time':i.end_time, 'price':i.price, 'name':i.name,'userID':id,'email':i.Email,'OrderDate':i.OrderDate,'HouseID':i.HouseID,'CardID':i.CardID,'Hname':i.Hname,'telephone':i.telephone, 'type': House.type, 'single_price': House.price, 'address': House.address, 'house_size': House.house_size, 'category': House.category, 'is_near_subway': House.is_near_subway, 'is_has_dw': House.is_has_dw, 'is_has_yt': House.is_has_yt, 'total_views': House.total_views,'style':House.style,'summary':House.summary,'rules':House.rules,'bed':House.bed,'OrderID':i.OrderID}
            list.append(d)
        result['len'] = len(list)
        result['list'] = list
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def contract_list_U(request):  # 查看合同列表
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        contracts=RContract.objects.filter(userID=id)
        list=[]
        result = {'result': 1, 'message': '查询成功！'}
        for i in contracts:
            order=Order.objects.get(OrderID=i.OrderID)
            if(order.OrderState==5):
                continue
            House=RHouse.objects.get(HouseID=i.HouseID)
            d = {'ContractID':i.ContractID,'start_time':i.start_time, 'end_time':i.end_time, 'price':i.price, 'name':i.name,'userID':id,'email':i.Email,'OrderDate':i.OrderDate,'HouseID':i.HouseID,'CardID':i.CardID,'Hname':i.Hname,'telephone':i.telephone, 'type': House.type, 'single_price': House.price, 'address': House.address, 'house_size': House.house_size, 'category': House.category, 'is_near_subway': House.is_near_subway, 'is_has_dw': House.is_has_dw, 'is_has_yt': House.is_has_yt, 'total_views': House.total_views,'style':House.style,'summary':House.summary,'rules':House.rules,'bed':House.bed,'OrderID':i.OrderID}
            list.append(d)
        result['len'] = len(list)
        result['list'] = list
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)



@csrf_exempt
def contract_delete(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            ContractID = int(data_json.get('ContractID'))
            if RContract.objects.filter(ContractID=ContractID).exists():
                RContract.objects.filter(ContractID=ContractID).delete()   
                result = {'result': 1, 'message': '删除成功'}
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '合同不存在'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def contract_info_M(request):  # 查看合同信息
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user=UserInfo.objects.get(userID=id)
        if(user.role!=1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result) 
        ContractID = int(data_json.get('ContractID'))
        if RContract.objects.filter(ContractID=ContractID).exists():
            contract=RContract.objects.get(ContractID=ContractID)
            House=RHouse.objects.get(HouseID=contract.HouseID)
            result={'result': 1, 'message': '获取成功','ContractID':contract.ContractID,'start_time':contract.start_time, 'end_time':contract.end_time, 'price':contract.price, 'name':contract.name,'userID':id,'OrderDate':contract.OrderDate,'HouseID':contract.HouseID,'CardID':contract.CardID,'Email':contract.Email,'name':contract.name,'Hname':contract.Hname,'telephone':contract.telephone,'type': House.type, 'single_price': House.price, 'address': House.address, 'house_size': House.house_size, 'category': House.category, 'is_near_subway': House.is_near_subway, 'is_has_dw': House.is_has_dw, 'is_has_yt': House.is_has_yt, 'total_views': House.total_views,'style':House.style,'summary':House.summary,'rules':House.rules,'bed':House.bed,'OrderID':contract.OrderID,'userID':contract.userID,'pdf':str(contract.OrderID)+'.pdf'}
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '合同不存在!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def generate_repair(request):  # 生成报修单
    if request.method == 'POST':
        token = request.POST.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            HouseID = int(request.POST.get('HouseID'))
            if(Repair.objects.filter(HouseID=HouseID,done=2,userID=id).exists()):
                result = {'result': 0, 'message': '正在维修!'}
                return JsonResponse(result)
            if Repair.objects.filter(HouseID=HouseID,done=1,userID=id).exists() == True:
                repair=Repair.objects.get(HouseID=HouseID,done=1,userID=id)
                House = RHouse.objects.get(HouseID=HouseID)
                description=request.POST.get('description')
                repair_time=request.POST.get('repair_time')
                source = request.FILES.get('file')
                user=UserInfo.objects.get(userID=id)
                repair.description=description
                repair.picture=source
                repair.address=House.address
                repair.telephone=user.telephone
                repair.repair_time=repair_time
                repair.save()
                result = {'result': 1, 'message': '报修成功','RepairID':repair.RepairID,'HouseID':HouseID,'userID':id,'description':description,'done':1,'address':House.address,'telephone':user.telephone, 'url': repair.get_photo_url,'repair_time':repair_time,'r_url':repair.get_re_photo_url}               
                return JsonResponse(result)
            else:
                House = RHouse.objects.get(HouseID=HouseID)
                description=request.POST.get('description')
                repair_time=request.POST.get('repair_time')
                source = request.FILES.get('file')
                user=UserInfo.objects.get(userID=id)
                repair=Repair.objects.create(HouseID=HouseID, userID=id, description=description, done=1,picture=source,address=House.address,telephone=user.telephone,repair_time=repair_time)
                result = {'result': 1, 'message': '报修成功','RepairID':repair.RepairID,'HouseID':HouseID,'userID':id,'description':description,'done':1,'address':House.address,'telephone':user.telephone, 'url': repair.get_photo_url,'repair_time':repair_time,'r_url': repair.get_re_photo_url}  
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def arrange(request):  # 安排师傅
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            RepairID = int(data_json.get('RepairID'))
            if Repair.objects.filter(RepairID=RepairID).exists() == True:
                repair = Repair.objects.get(RepairID=RepairID)
                operatorID = int(data_json.get('operatorID'))
                repair.operatorID=operatorID
                repair.done=2
                repair.save()
                result = {'result': 1, 'message': '安排成功','RepairID':RepairID,'HouseID':repair.HouseID,'userID':repair.userID,'description':repair.description,'done':2, 'url':repair.get_photo_url,'operatorID':repair.operatorID}
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '工单不存在'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def repair_list(request):  # 报修单列表
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            repairs=Repair.objects.all()
            list=[]
            result = {'result': 1, 'message': '查询成功！'}
            for i in repairs:
                House=RHouse.objects.get(HouseID=i.HouseID)
                user=UserInfo.objects.get(userID=i.userID)
                b=i.get_operatorID
                if(b!=-1):
                    sf=UserInfo.objects.get(userID=i.operatorID)
                    sfname=sf.username
                else:
                    sfname=-1
                d = {'RepairID':i.RepairID,'HouseID':i.HouseID,'userID':i.userID,'description':i.description,'done':i.done,'address':i.address,'telephone':i.telephone, 'url': i.get_photo_url,'operatorID':i.get_operatorID,'reply':i.reply,'comment':i.comment,'telephone':i.telephone,'repair_time':i.repair_time,'name':user.username,'sfname':sfname,'Hname':House.name,'r_url': i.get_re_photo_url}      
                list.append(d)
            result['len'] = len(list)
            result['list'] = list
            return JsonResponse(result)     
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def repair_info(request):  # 报修单详细
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        RepairID = int(data_json.get('RepairID'))
        if Repair.objects.filter(RepairID=RepairID).exists():
            repair=Repair.objects.get(RepairID=RepairID)
            House=RHouse.objects.get(HouseID=repair.HouseID)
            userID = repair.userID
            user = UserInfo.objects.get(userID=userID)
            b=repair.get_operatorID
            if(b!=-1):
                sf=UserInfo.objects.get(userID=repair.operatorID)
                sfname=sf.username
            else:
                sfname=-1
            result={'result': 1, 'message': '查询成功','RepairID':repair.RepairID,'HouseID':repair.HouseID,'userID':repair.userID,'description':repair.description,'done':repair.done,'address':repair.address,'telephone':repair.telephone, 'url': repair.get_photo_url,'operatorID':repair.get_operatorID,'reply':repair.reply,'comment':repair.comment,'repair_time':repair.repair_time,'name':user.username,'sfname':sfname,'Hname':House.name,'r_url': repair.get_re_photo_url}      
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '工单不存在!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def repair_list_U(request):  # 报修单列表
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            repairs=Repair.objects.filter(userID=id)
            list=[]
            result = {'result': 1, 'message': '查询成功！'}
            for i in repairs:
                House=RHouse.objects.get(HouseID=i.HouseID)
                user=UserInfo.objects.get(userID=id)
                b=i.get_operatorID
                if(b!=-1):
                    sf=UserInfo.objects.get(userID=i.operatorID)
                    sfname=sf.username
                else:
                    sfname=-1
                d = {'RepairID':i.RepairID,'HouseID':i.HouseID,'userID':i.userID,'description':i.description,'done':i.done,'address':i.address,'telephone':i.telephone, 'url': i.get_photo_url,'operatorID':i.get_operatorID,'reply':i.reply,'comment':i.comment,'telephone':i.telephone,'repair_time':i.repair_time,'name':user.username,'sfname':sfname,'Hname':House.name,'r_url': i.get_re_photo_url}        
                list.append(d)
            result['len'] = len(list)
            result['list'] = list
            return JsonResponse(result)     
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def repair_list_M(request):  # 报修单列表
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            repairs = Repair.objects.filter(operatorID=id)
            list=[]
            result = {'result': 1, 'message': '查询成功！'}
            for i in repairs:
                House=RHouse.objects.get(HouseID=i.HouseID)
                user=UserInfo.objects.get(userID=i.userID)
                b=i.get_operatorID
                if(b!=-1):
                    sf=UserInfo.objects.get(userID=i.operatorID)
                    sfname=sf.username
                else:
                    sfname=-1
                d = {'RepairID':i.RepairID,'HouseID':i.HouseID,'userID':i.userID,'description':i.description,'done':i.done,'address':i.address,'telephone':i.telephone, 'url':i.get_photo_url,'operatorID':i.get_operatorID,'reply':i.reply,'comment':i.comment,'telephone':i.telephone,'repair_time':i.repair_time,'name':user.username,'sfname':sfname,'Hname':House.name,'r_url': i.get_re_photo_url} 
                list.append(d)
            result['len'] = len(list)
            result['list'] = list
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def repair_info_U(request):  # 报修单详细
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        HouseID = int(data_json.get('HouseID'))
        if Repair.objects.filter(userID=id,HouseID=HouseID,done=1).exists():
            repair= Repair.objects.get(userID=id,HouseID=HouseID,done=1)
            House=RHouse.objects.get(HouseID=repair.HouseID)
            user=UserInfo.objects.get(userID=repair.userID)
            b=repair.get_operatorID
            if(b!=-1):
                sf=UserInfo.objects.get(userID=repair.operatorID)
                sfname=sf.username
            else:
                sfname=-1
            result={'result': 1, 'message': '查询成功','RepairID':repair.RepairID,'HouseID':repair.HouseID,'userID':repair.userID,'description':repair.description,'done':repair.done,'address':repair.address,'telephone':repair.telephone, 'url': repair.get_photo_url,'operatorID':repair.get_operatorID,'reply':repair.reply,'comment':repair.comment,'repair_time':repair.repair_time,'name':user.username,'sfname':sfname,'Hname':House.name,'r_url': repair.get_re_photo_url}     
            return JsonResponse(result)
        elif Repair.objects.filter(userID=id,HouseID=HouseID,done=2).exists():
            repair= Repair.objects.get(userID=id,HouseID=HouseID,done=2)
            House=RHouse.objects.get(HouseID=repair.HouseID)
            user=UserInfo.objects.get(userID=repair.userID)
            b=repair.get_operatorID
            if(b!=-1):
                sf=UserInfo.objects.get(userID=repair.operatorID)
                sfname=sf.username
            else:
                sfname=-1
            result={'result': 1, 'message': '查询成功','RepairID':repair.RepairID,'HouseID':repair.HouseID,'userID':repair.userID,'description':repair.description,'done':repair.done,'address':repair.address,'telephone':repair.telephone, 'url':repair.get_photo_url,'operatorID':repair.get_operatorID,'reply':repair.reply,'comment':repair.comment,'repair_time':repair.repair_time,'name':user.username,'sfname':sfname,'Hname':House.name,'r_url': repair.get_re_photo_url}     
            return JsonResponse(result)
        elif Repair.objects.filter(userID=id,HouseID=HouseID,done=3).exists():
            repair= Repair.objects.get(userID=id,HouseID=HouseID,done=3)
            House=RHouse.objects.get(HouseID=repair.HouseID)
            user=UserInfo.objects.get(userID=repair.userID)
            b=repair.get_operatorID
            if(b!=-1):
                sf=UserInfo.objects.get(userID=repair.operatorID)
                sfname=sf.username
            else:
                sfname=-1
            result={'result': 1, 'message': '查询成功','RepairID':repair.RepairID,'HouseID':repair.HouseID,'userID':repair.userID,'description':repair.description,'done':repair.done,'address':repair.address,'telephone':repair.telephone, 'url':repair.get_photo_url,'operatorID':repair.get_operatorID,'reply':repair.reply,'comment':repair.comment,'repair_time':repair.repair_time,'name':user.username,'sfname':sfname,'Hname':House.name,'r_url': repair.get_re_photo_url}     
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '报修单不存在!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def repair_delete_U(request):  # 报修单撤回
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        RepairID = int(data_json.get('RepairID'))
        if Repair.objects.filter(RepairID=RepairID).exists():
            repair=Repair.objects.get(RepairID=RepairID)
            repair.delete()
            result={'result': 1, 'message': '删除成功'}      
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '工单不存在!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def generate_complaint(request):  # 生成投诉
    if request.method == 'POST':
        token = request.POST.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            HouseID = int(request.POST.get('HouseID'))
            if Complaint.objects.filter(HouseID=HouseID,done=1,userID=id).exists() == True:
                complaint=Complaint.objects.get(HouseID=HouseID,done=1,userID=id)
                House = RHouse.objects.get(HouseID=HouseID)
                description=request.POST.get('description')
                source = request.FILES.get('file')
                user=UserInfo.objects.get(userID=id)
                complaint.description=description
                complaint.picture=source
                complaint.address=House.address
                complaint.telephone=user.telephone
                complaint.save()
                result = {'result': 1, 'message': '投诉成功','ComplaintID':complaint.ComplaintID,'HouseID':HouseID,'userID':id,'description':description,'done':1,'address':House.address,'telephone':user.telephone, 'url':complaint.get_photo_url}               
                return JsonResponse(result)
            else:
                House = RHouse.objects.get(HouseID=HouseID)
                description=request.POST.get('description')
                source = request.FILES.get('file')
                user=UserInfo.objects.get(userID=id)
                Complaint.objects.create(HouseID=HouseID, userID=id, description=description, done=1,picture=source,address=House.address,telephone=user.telephone)
                result = {'result': 1, 'message': '投诉成功'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def complaint_list_U(request):  # 投诉单列表
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            complaints=Complaint.objects.filter(userID=id)
            list=[]
            result = {'result': 1, 'message': '查询成功！'}
            for i in complaints:
                House=RHouse.objects.get(HouseID=i.HouseID)
                user=UserInfo.objects.get(userID=id)
                d = {'ComplaintID':i.ComplaintID,'HouseID':i.HouseID,'userID':i.userID,'description':i.description,'done':i.done,'address':i.address,'telephone':i.telephone, 'url':i.get_photo_url,'reply':i.reply,'name':user.username,'Hname':House.name}        
                list.append(d)
            result['len'] = len(list)
            result['list'] = list
            return JsonResponse(result)      
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def complaint_info_U(request):  # 投诉单详细
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        HouseID = int(data_json.get('HouseID'))
        if Complaint.objects.filter(userID=id,HouseID=HouseID,done=1).exists():
            complaint= Complaint.objects.get(userID=id,HouseID=HouseID,done=1)
            House=RHouse.objects.get(HouseID=complaint.HouseID)
            user=UserInfo.objects.get(userID=complaint.userID)
            result={'result': 1, 'message': '查询成功','ComplaintID':complaint.ComplaintID,'HouseID':complaint.HouseID,'userID':complaint.userID,'description':complaint.description,'done':complaint.done,'address':complaint.address,'telephone':complaint.telephone, 'url':complaint.get_photo_url,'reply':complaint.reply,'name':user.username,'Hname':House.name}     
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '投诉单不存在!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def complaint_delete_U(request):  # 投诉单撤回
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        ComplaintID = int(data_json.get('ComplaintID'))
        if Complaint.objects.filter(ComplaintID=ComplaintID).exists():
            complaint=Complaint.objects.get(ComplaintID=ComplaintID)
            complaint.delete()
            result={'result': 1, 'message': '删除成功'}      
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '投诉不存在!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def complaint_list(request):  # 投诉单列表
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            complaints=Complaint.objects.all()
            list=[]
            result = {'result': 1, 'message': '查询成功！'}
            for i in complaints:
                user=UserInfo.objects.get(userID=i.userID)
                House=RHouse.objects.get(HouseID=i.HouseID)
                d = {'ComplaintID':i.ComplaintID,'HouseID':i.HouseID,'userID':i.userID,'description':i.description,'done':i.done,'address':i.address,'telephone':i.telephone, 'url':i.get_photo_url,'reply':i.reply,'name':user.username,'Hname':House.name}      
                list.append(d)
            result['len'] = len(list)
            result['list'] = list
            return JsonResponse(result)     
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def complaint_info(request):  # 投诉单详细
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user=UserInfo.objects.get(userID=id)
        if(user.role!=1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result) 
        ComplaintID = int(data_json.get('ComplaintID'))
        if Complaint.objects.filter(ComplaintID=ComplaintID).exists():
            complaint=Complaint.objects.get(ComplaintID=ComplaintID)
            user=UserInfo.objects.get(userID=complaint.userID)
            House=RHouse.objects.get(HouseID=complaint.HouseID)
            result={'result': 1, 'message': '查询成功','ComplaintID':complaint.ComplaintID,'HouseID':complaint.HouseID,'userID':complaint.userID,'description':complaint.description,'done':complaint.done,'address':complaint.address,'telephone':complaint.telephone, 'url':complaint.get_photo_url,'reply':complaint.reply,'name':user.username,'Hname':House.name,'email':user.email}      
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '投诉不存在!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def reply(request):  # 回复投诉
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            ComplaintID = int(data_json.get('ComplaintID'))
            if Complaint.objects.filter(ComplaintID=ComplaintID).exists() == True:
                complaint = Complaint.objects.get(ComplaintID=ComplaintID)
                reply = data_json.get('reply')
                complaint.reply=reply
                complaint.done=2
                complaint.save()
                result = {'result': 1, 'message': '回复成功','ComplaintID':complaint.ComplaintID,'HouseID':complaint.HouseID,'userID':complaint.userID,'description':complaint.description,'done':0,'userID':complaint.userID, 'url': complaint.get_photo_url,'reply':complaint.reply}
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '工单不存在'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def addMaster(request):  # 导入师傅
    if request.method == 'POST':
        data_json = json.loads(request.body)
        username = data_json.get('username')
        telephone = data_json.get('phone')
        password = data_json.get('password')
        sex = data_json.get('sex')
        email = data_json.get('email')
        role = 3
        if UserInfo.objects.filter(telephone=telephone).exists():
            return JsonResponse({'result': 0, 'message': "手机已存在!"})
        elif UserInfo.objects.filter(email=email).exists():
            return JsonResponse({'result': 0, 'message': "邮箱已存在!"})
        else:
            all = UserInfo.objects.all()
            count = len(all)
            new_user = UserInfo(userID=count, username=username,
                                password=password, telephone=telephone, role=role, sex=sex, email=email)
            new_user.save()
        return JsonResponse({'result': 1, 'message': "导入成功!"})
    else:
        return JsonResponse({'result': 0, 'message': "前端炸了!"})

@csrf_exempt
def delMaster(request):  # 删除师傅
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user = UserInfo.objects.get(userID=id)
        if(user.role != 1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result)
        else:
            userID = int(data_json.get('userID'))
            if UserInfo.objects.filter(userID=userID).exists():
                UserInfo.objects.filter(userID=userID).delete()   
                result = {'result': 1, 'message': '删除成功'}
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '师傅不存在'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def reply_G(request):  # 回复工单
    if request.method == 'POST':
        #data_json = json.loads(request.body)
        token = request.POST.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            RepairID = int(request.POST.get('RepairID'))
            if Repair.objects.filter(RepairID=RepairID).exists() == True:
                repair = Repair.objects.get(RepairID=RepairID)
                reply = request.POST.get('reply')
                repair.operatorID = id
                repair.reply = reply
                repair.done=3
                source = request.FILES.get('file')
                repair.re_picture = source
                repair.save()
                result = {'result': 1, 'message': '回复成功'}
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '工单不存在'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def comment(request):  # 评价工单
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            RepairID = int(data_json.get('RepairID'))
            if Repair.objects.filter(RepairID=RepairID).exists() == True:
                repair = Repair.objects.get(RepairID=RepairID)
                comment = data_json.get('comment')
                repair.comment = comment
                repair.done=4
                repair.save()
                result = {'result': 1, 'message': '评价成功'}
                return JsonResponse(result)
            else:
                result = {'result': 0, 'message': '工单不存在'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


rule = [
    '1、本合同由青年租房管理系统提供，仅限在中国大陆有固定居住地（常住）的人士签订。',
    '2、本合同保障地区范围为中国大陆境内（不包含香港、澳门、台湾地区）。',
    '3、本合同支付人为经中国人民银行批准的支付机构。',
    '4、本合同期限为租客在平台发起交易指令时（以该行为所处时间点为准）起168小时内（含）。',
    '5、在租房期限内，租客通过合同载明的非金融机构完成支付，如支付资金实际到达收款人账户的时间超过下单起期后12小时（含12小时）未到账，公司按照本合同约定的金额对租客进行赔偿。',
    '6、本合同仅承担因支付平台本身的原因造成的支付到账延迟责任，因下列原因导致的迟延到账损失，公司不负责赔偿：（ 1） 租客操作失误；（ 2）租客自身账户问题；（ 3）结算银行否认交易；（ 4）支付被依法认定为无效或被撤销的；（ 5） 租客交易账户异常（详见条款释义）；（6）银行系统原因、中国人民银行支付清算系统原因等其他非支付机构的系统原因。'
]

@csrf_exempt
def gen_pdf(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        OrderID = int(data_json.get('OrderID'))
        order=Order.objects.get(OrderID=OrderID)
        story = []
        title_style = ParagraphStyle(name="TitleStyle", fontName="msyh", fontSize=10, alignment=TA_CENTER, )
        content_style = ParagraphStyle(name="ContentStyle",
                                    fontName="msyh",
                                    fontSize=7,
                                    alignment=TA_LEFT, )
        content_style_1 = ParagraphStyle(name="ContentStyle",
                                        fontName="msyh",
                                        fontSize=9,
                                        leftIndent=20,
                                        alignment=TA_LEFT, )
        content_style_line = ParagraphStyle(name="ContentStyle",
                                            fontName="msyh",
                                            fontSize=9,
                                            underlineOffset=-3,
                                            alignment=TA_LEFT, )
        content_style_line_1 = ParagraphStyle(name="ContentStyle",
                                            fontName="msyh",
                                            fontSize=7,
                                            underlineOffset=-3,
                                            alignment=TA_LEFT, )
        task_data = [['房间名称', '开始时间', '结束时间'],
                    [order.Hname, order.start_time,order.end_time],
                    ]
        basic_style = TableStyle([('FONTNAME', (0, 0), (-1, -1), 'msyh'),
                                ('FONTSIZE', (0, 0), (-1, -1), 7),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                                # 'SPAN' (列,行)坐标
                                ('SPAN', (1, 0), (2, 0)),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                ])
        story.append(Spacer(1, 10 * mm))
        story.append(Paragraph("合同", title_style))
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("单位名称： 青年租房管理系统", content_style))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph("订单编号： <u> {} </u>".format(order.OrderID), content_style))
        story.append(Spacer(1, 2 * mm))
        story.append(
            Paragraph("<u>租客可于当晚前往青年租房管理系统官网（http://43.138.77.8/dz/roomhubSite/） 查询详细的凭证信息。</u>",
                    content_style_line))
        story.append(Spacer(1, 2 * mm, isGlue=True))
        story.append(
            Paragraph("租客姓名:"+ order.name+"&nbsp&nbsp&nbsp" +"证件类型：居民身份证 &nbsp&nbsp&nbsp 证件号码："+ order.CardID, content_style))
        story.append(Paragraph("租客电话：" +order.telephone+"&nbsp&nbsp&nbsp" +"租客邮箱"+order.Email, content_style))
        story.append(Paragraph("保险期间：自北京时间起  "+str(order.start_time)+" 至  "+str(order.end_time)+" 时止", content_style))
        story.append(Paragraph("支付时间：  "+str(order.OrderDate)+" 约定到账周期： 3 天  支付方式： 银行汇款", content_style))
        task_table = Table(task_data, colWidths=[75 * mm, 50 * mm, 40 * mm], rowHeights=8 * mm, style=basic_style)
        story.append(task_table)
        story.append(Paragraph("总金额： &nbsp&nbsp "+str(order.price)+" 元", content_style))
        story.append(Paragraph("条款适用： 青年租房管理系统《非金融机构支付服务保险条款》", content_style_line_1))
        story.append(Paragraph(
            "<u>_____________________________________________________________________________________________________________________________________________________</u>",
            content_style_line_1))
        story.append(Paragraph("特别约定：", content_style))
        for item in rule:
            story.append(Paragraph(item, content_style))
        story.append(Paragraph(
            "<u>_____________________________________________________________________________________________________________________________________________________</u>",
            content_style_line_1))
        story.append(Paragraph('合同争议解决方式： 诉讼 付款方式：趸缴', content_style))
        doc = SimpleDocTemplate(str(order.OrderID)+".pdf",
                                leftMargin=20 * mm, rightMargin=20 * mm, topMargin=2 * mm, bottomMargin=20 * mm)
        doc.build(story)
        result = {'result': 1, 'message': '生成成功!','url':"/home/xw/roomhub/"+(str(order.OrderID)+".pdf" )}
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def download_template(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        OrderID = int(data_json.get('OrderID'))
        order=Order.objects.get(OrderID=OrderID)
        contract=RContract.objects.get(OrderID=OrderID)
        if(order.OrderState==5):
            file = open(str(OrderID)+".pdf", 'rb')
            response = FileResponse(file)
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename=str(OrderID)+".pdf"'
            return response
        else:
            file = open("."+contract.contract.url, 'rb')
            response = FileResponse(file)
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename=str(OrderID)+".pdf"'
            return response

    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def first_page(request):  # 首页内容
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            result = {'result': 1, 'message': '查询成功!'}
            result['u_num']=UserInfo.objects.filter(role=2).count()
            result['w_num']=UserInfo.objects.filter(role=3).count()
            result['l_num']=RHouse.objects.filter(type="长租").count()
            result['s_num']=RHouse.objects.filter(type="短租").count()
            begin = datetime.date.today()
            orders=Order.objects.all()
            l = []       
            for j in range(0, 6):
                end = begin - relativedelta(months=j)
                start = begin - relativedelta(months=j+1)
                sign = 0
                for k in orders:
                    House = RHouse.objects.get(HouseID=k.HouseID)
                    if(House.type!="长租"):
                        continue
                    time = k.OrderDate.strftime('%Y-%m-%d')
                    if start <= datetime.date(*map(int, time.split('-'))) <= end:
                        sign=sign+1
                l.append(sign)        
            result["l"]=list(reversed(l))     
            s = []       
            for j in range(0, 6):
                end = begin - relativedelta(months=j)
                start = begin - relativedelta(months=j+1)
                sign = 0
                for k in orders:
                    House = RHouse.objects.get(HouseID=k.HouseID)
                    if(House.type!="短租"):
                        continue
                    time = k.OrderDate.strftime('%Y-%m-%d')            
                    if start <= datetime.date(*map(int, time.split('-'))) <= end:
                        sign=sign+1
                s.append(sign)        
            result["s"]=list(reversed(s))     
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)
        
@csrf_exempt
def worker_list(request):  # 查看租客列表
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        user=UserInfo.objects.get(userID=id)
        if(user.role!=1):
            result = {'result': 0, 'message': '没有权限'}
            return JsonResponse(result)
        users=UserInfo.objects.filter(role=3)
        list=[]
        result = {'result': 1, 'message': '查询成功！'}
        for i in users:
            d = {'username': i.username, 'userID': i.userID,'url': 'https://z3.ax1x.com/2021/06/09/2cTNY4.png', 'email': i.email, 'role': i.role,'money':i.money,'age':i.age,'sex':i.sex,'telephone':i.telephone,'birth':i.birth,'password':i.password}
            list.append(d)
        result['len'] = len(list)
        result['list'] = list
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)



@csrf_exempt
def allhouse_M(request):  # 查询所有房间
    if request.method == 'POST':
        token = request.META.get('HTTP_AUTHORIZATION', 0)
        id = Check(token)
        if id == -1:
            result = {'result': 1, 'message': 'Token有误!'}
            all = RHouse.objects.all()
            house = []
            for i in all:
                d = {}
                d["HouseID"] = i.HouseID
                d["price"] = i.price
                d["name"] = i.name
                d["type"] = i.type
                d["style"] = i.style
                d["address"] = i.address
                d["house_size"] = i.house_size
                d["category"] = i.category
                d["is_near_subway"] = i.is_near_subway
                d["is_has_dw"] = i.is_has_dw
                d["is_has_yt"] = i.is_has_yt
                d["total_views"] = i.total_views
                d["is_collect"]=0
                if RImg.objects.filter(imgid=i.HouseID).exists() == True:
                    imgs = RImg.objects.filter(imgid=i.HouseID)
                    d["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url
                else:
                    d["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"
                if(type==1):
                    begin = date.today()
                    end=begin + timedelta(days=30)
                    exist = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3).first()
                    s=""
                    if exist:
                        order = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3)
                        for j in range((end - begin).days+1):
                            day = begin + datetime.timedelta(days=j)
                            sign=0
                            for k in order:
                                start=k.start_time
                                end=k.end_time
                                if start<=day<=end:  
                                    sign=1
                                    break
                            if sign==1:
                                s+='1'    
                            else:
                                s+='0'                            
                    else:
                        s="000000000000000000000000000000"           
                else:
                    begin = date.today()
                    end=begin + relativedelta(months=12)
                    exist = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3).first()
                    s=""
                    if exist:
                        order = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3)
                        for j in range(0,12):
                            day=begin + relativedelta(months=j)
                            sign=0
                            for k in order:
                                start=k.start_time
                                end=k.end_time
                                if start<=day<=end:  
                                    sign=1
                                    break
                            if sign==1:
                                s+='1'    
                            else:
                                s+='0' 
                    else:
                        s="000000000000000000000000000000"    
                d["s"] = s            
                house.append(d)
            result["house"] = house
            return JsonResponse(result)
        result = {'result': 1, 'message': '获取成功!'}
        user=UserInfo.objects.get(userID=id)
        all = RHouse.objects.all()
        house = []
        for i in all:
            d = {}
            d["HouseID"] = i.HouseID
            d["price"] = i.price
            d["name"] = i.name
            d["type"] = i.type
            d["style"] = i.style
            d["address"] = i.address
            d["house_size"] = i.house_size
            d["category"] = i.category
            d["is_near_subway"] = i.is_near_subway
            d["is_has_dw"] = i.is_has_dw
            d["is_has_yt"] = i.is_has_yt
            d["total_views"] = i.total_views
            d["status"]=i.status
            if RCollect.objects.filter(userID=id, HouseID=i.HouseID).exists() == True:
                d["is_collect"]=1
            else:
                d["is_collect"]=0
            if RImg.objects.filter(HouseID=i.HouseID).exists() == True:
                imgs = RImg.objects.filter(HouseID=i.HouseID)
                d["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url                                 
            else:
                d["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"
            if(type==1):
                begin = date.today()
                end=begin + timedelta(days=30)
                exist = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3).first()
                s=""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3)
                    for j in range((end - begin).days+1):
                        day = begin + datetime.timedelta(days=j)
                        sign=0
                        for k in order:
                            start=k.start_time
                            end=k.end_time
                            if start<=day<=end:  
                                sign=1
                                break
                        if sign==1:
                            s+='1'    
                        else:
                            s+='0'                            
                else:
                    s="000000000000000000000000000000"           
            else:
                begin = date.today()
                end=begin + relativedelta(months=12)
                exist = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3).first()
                s=""
                if exist:
                    order = Order.objects.filter(HouseID=i.HouseID).exclude(OrderState=3)
                    for j in range(0,12):
                        day=begin + relativedelta(months=j)
                        sign=0
                        for k in order:
                            start=k.start_time
                            end=k.end_time
                            if start<=day<=end:  
                                sign=1
                                break
                        if sign==1:
                            s+='1'    
                        else:
                            s+='0' 
                else:
                    s="000000000000000000000000000000"    
            d["s"] = s            
            house.append(d)
        result["house"] = house
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def repair_list_N(request):  # 报修单列表
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            repairs=Repair.objects.filter(done=1)
            list=[]
            result = {'result': 1, 'message': '查询成功！'}
            for i in repairs:
                House=RHouse.objects.get(HouseID=i.HouseID)
                user=UserInfo.objects.get(userID=i.userID)
                b=i.get_operatorID
                if(b!=-1):
                    sf=UserInfo.objects.get(userID=i.operatorID)
                    sfname=sf.username
                else:
                    sfname=-1
                d = {'RepairID':i.RepairID,'HouseID':i.HouseID,'userID':i.userID,'description':i.description,'done':i.done,'address':i.address,'telephone':i.telephone, 'url':i.get_photo_url,'operatorID':i.get_operatorID,'reply':i.reply,'comment':i.comment,'telephone':i.telephone,'repair_time':i.repair_time,'name':user.username,'sfname':sfname,'Hname':House.name,'r_url': i.get_re_photo_url}      
                list.append(d)
            result['len'] = len(list)
            result['list'] = list
            return JsonResponse(result)     
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def upload_avatars_M(request):  # 修改头像
    if request.method == 'POST':
        token = request.POST.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        source = request.FILES.get('file')
        userID = int(request.POST.get('userID'))
        if source:
            if UserInfo.objects.filter(userID=userID).exists() == True:
                user = UserInfo.objects.get(userID=userID)
                user.header = source
                user.save()
                result = {'result': 1, 'id': id,  'url': 'http://43.138.77.8/dz/roomhubSite'+user.header.url}
            else:
                result = {'result': 0, 'message': '未找到该用户!'}
            return JsonResponse(result)
        else:
            result = {'result': 0, 'message': '请检查上传内容!'}
            return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def orderlist_M(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        Orders=Order.objects.all()
        list=[]
        result = {'result': 1, 'message': '查询成功！'}
        for i in Orders:
            House=RHouse.objects.get(HouseID=i.HouseID)
            d = {'OrderID': i.OrderID, 'OrderState': i.OrderState, 'HouseID': i.HouseID, 'userID': i.userID, 'OrderDate': i.OrderDate, 'Email': i.Email, 'CardID': i.CardID,
                 'name': i.name, 'Hname': i.Hname, 'telephone': i.telephone, 'start_time': i.start_time, 'end_time': i.end_time,'price':i.price,'see':i.see,'address':House.address,'single_price':House.price,'house_size':House.house_size,'status':House.status,'category':House.category,'type':House.type,'is_near_subway':House.is_near_subway,'is_has_dw':House.is_has_dw,'is_has_yt':House.is_has_yt,'total_views':House.total_views,'style':House.style,'summary':House.summary,'rules':House.rules,'bed':House.bed}
            if RImg.objects.filter(imgid=i.HouseID).exists() == True:
                imgs = RImg.objects.filter(imgid=i.HouseID)
                d["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url    
            else:
                d["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"
            list.append(d)
        result['len'] = len(list)
        result['list'] = list
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


from alipay import AliPay, AliPayConfig


@csrf_exempt
def get(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        OrderID = data_json.get('OrderID')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        order = Order.objects.get(OrderID=OrderID)
        app_private_key_string = settings.app_private_key_string
        alipay_public_key_string = settings.alipay_public_key_string
        # 4. 创建支付宝实例
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG,  # 默认False
            config=AliPayConfig(timeout=1000)  # 可选, 请求超时时间
        )
        # 5. 调用支付宝的支付方法
        # 如果你是 Python 3的用户，使用默认的字符串即可
        subject = "租房管理系统测试订单"
        order.cnt=order.cnt+1
        order.save()
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        # https://openapi.alipay.com/gateway.do 这个是线上的
        # 'https://openapi.alipaydev.com/gateway.do' 这个是沙箱的
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=random.randrange(0,10000000),
            total_amount=str(order.price),  # 一定要进行类型转换,因为decimal不是基本数据类型
            subject=subject,
            return_url=settings.ALIPAY_RETURN_URL+str(order.OrderID),  # 支付成功之后,跳转的页面
            # notify_url="https://example.com/notify"  # 可选, 不填则使用默认notify url
        )
        # 6.  拼接连接
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        # 7. 返回响应
        return JsonResponse({'result': 1, 'message': '操作成功!', 'alipay_url': pay_url})

    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def put(request):
    # 1. 接收数据
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        # 2. 查询字符串转换为字典 验证数据

        # 3. 验证没有问题获取支付宝交易流水号
        signature =  data_json.pop("sign")
        OrderID = data_json.get('OrderID')
        app_private_key_string = settings.app_private_key_string
        alipay_public_key_string = settings.alipay_public_key_string
        # 创建支付宝实例
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG,  # 默认False
            config=AliPayConfig(timeout=1000)  # 可选, 请求超时时间
        )
        success = alipay.verify(data_json, signature)

        Order.objects.filter(OrderID=OrderID).update(OrderState=4)
        return JsonResponse({'result': 1, 'message': '支付成功!'})
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def orderlist_M_1(request):
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        Orders=Order.objects.filter(OrderState=1)
        list=[]
        result = {'result': 1, 'message': '查询成功！'}
        for i in Orders:
            House=RHouse.objects.get(HouseID=i.HouseID)
            d = {'OrderID': i.OrderID, 'OrderState': i.OrderState, 'HouseID': i.HouseID, 'userID': i.userID, 'OrderDate': i.OrderDate, 'Email': i.Email, 'CardID': i.CardID,
                 'name': i.name, 'Hname': i.Hname, 'telephone': i.telephone, 'start_time': i.start_time, 'end_time': i.end_time,'price':i.price,'see':i.see,'address':House.address,'single_price':House.price,'house_size':House.house_size,'status':House.status,'category':House.category,'type':House.type,'is_near_subway':House.is_near_subway,'is_has_dw':House.is_has_dw,'is_has_yt':House.is_has_yt,'total_views':House.total_views,'style':House.style,'summary':House.summary,'rules':House.rules,'bed':House.bed}
            if RImg.objects.filter(imgid=i.HouseID).exists() == True:
                imgs = RImg.objects.filter(imgid=i.HouseID)
                d["urls"] = 'http://43.138.77.8/dz/roomhubSite'+imgs[0].img.url    
            else:
                d["urls"] = "https://z3.ax1x.com/2021/06/09/2cqBCD.png"
            list.append(d)
        result['len'] = len(list)
        result['list'] = list
        return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def complaint_list_M_1(request):  # 投诉单列表
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            complaints=Complaint.objects.filter(done=1)
            list=[]
            result = {'result': 1, 'message': '查询成功！'}
            for i in complaints:
                user=UserInfo.objects.get(userID=i.userID)
                House=RHouse.objects.get(HouseID=i.HouseID)
                d = {'ComplaintID':i.ComplaintID,'HouseID':i.HouseID,'userID':i.userID,'description':i.description,'done':i.done,'address':i.address,'telephone':i.telephone, 'url':i.get_photo_url,'reply':i.reply,'name':user.username,'Hname':House.name,'email':user.email}      
                list.append(d)
            result['len'] = len(list)
            result['list'] = list
            return JsonResponse(result)     
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)

@csrf_exempt
def upload_contract(request):  
    if request.method == 'POST':
        source = request.FILES.get('file')
        OrderID = request.POST.get('OrderID')
        order=Order.objects.get(OrderID=OrderID)
        order.OrderState=4
        order.save()
        contract=RContract.objects.get(OrderID=OrderID)
        contract.contract=source
        contract.save()
        result = {'result': 1, 'message': '上传成功!'}
        return JsonResponse(result)     
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)


@csrf_exempt
def generate_order_M(request):  
    if request.method == 'POST':
        data_json = json.loads(request.body)
        token = data_json.get('token')
        id = Check(token)
        if id == -1:
            result = {'result': 0, 'message': 'Token有误!'}
            return JsonResponse(result)
        else:
            userID=int(data_json.get('userID'))
            HouseID=int(data_json.get('HouseID'))
            if RHouse.objects.filter(HouseID=HouseID).exists() == True:
                House = RHouse.objects.get(HouseID=HouseID)
                if House.status == 2:
                    result = {'result': 0, 'message': '房间已租'}
                    return JsonResponse(result)
                elif House.status == 3:
                    result = {'result': 0, 'message': '房间暂停出售'}
                else:
                    start_time = data_json.get('start_time')
                    end_time = data_json.get('end_time')
                    price = int(data_json.get('price'))
                    idcard=data_json.get('CardID')
                    user = UserInfo.objects.get(userID=userID)
                    email = user.email
                    Hname=House.name
                    telephone=data_json.get('telephone')
                    name=data_json.get('name')

                    order=Order.objects.create(start_time=start_time, end_time=end_time, price=price, name=name, userID=userID,Email=email,Hname=Hname,CardID=idcard,telephone=telephone,OrderState=1,see=1,HouseID=HouseID)
                    if(House.type=="长租"):
                        order.OrderState=5
                        order.save()
                        story = []
                        title_style = ParagraphStyle(name="TitleStyle", fontName="msyh", fontSize=10, alignment=TA_CENTER, )
                        content_style = ParagraphStyle(name="ContentStyle",
                                                    fontName="msyh",
                                                    fontSize=7,
                                                    alignment=TA_LEFT, )
                        content_style_1 = ParagraphStyle(name="ContentStyle",
                                                        fontName="msyh",
                                                        fontSize=9,
                                                        leftIndent=20,
                                                        alignment=TA_LEFT, )
                        content_style_line = ParagraphStyle(name="ContentStyle",
                                                            fontName="msyh",
                                                            fontSize=9,
                                                            underlineOffset=-3,
                                                            alignment=TA_LEFT, )
                        content_style_line_1 = ParagraphStyle(name="ContentStyle",
                                                            fontName="msyh",
                                                            fontSize=7,
                                                            underlineOffset=-3,
                                                            alignment=TA_LEFT, )
                        task_data = [['房间名称', '开始时间', '结束时间'],
                                    [order.Hname, order.start_time,order.end_time],
                                    ]
                        basic_style = TableStyle([('FONTNAME', (0, 0), (-1, -1), 'msyh'),
                                                ('FONTSIZE', (0, 0), (-1, -1), 7),
                                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                                                # 'SPAN' (列,行)坐标
                                                ('SPAN', (1, 0), (2, 0)),
                                                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                                ])
                        story.append(Spacer(1, 10 * mm))
                        story.append(Paragraph("合同", title_style))
                        story.append(Spacer(1, 5 * mm))
                        story.append(Paragraph("单位名称： 青年租房管理系统", content_style))
                        story.append(Spacer(1, 2 * mm))
                        story.append(Paragraph("订单编号： <u> {} </u>".format(order.OrderID), content_style))
                        story.append(Spacer(1, 2 * mm))
                        story.append(
                            Paragraph("<u>租客可于当晚前往青年租房管理系统官网（http://43.138.77.8/dz/roomhubSite/） 查询详细的凭证信息。</u>",
                                    content_style_line))
                        story.append(Spacer(1, 2 * mm, isGlue=True))
                        story.append(
                            Paragraph("租客姓名:"+ order.name+"&nbsp&nbsp&nbsp" +"证件类型：居民身份证 &nbsp&nbsp&nbsp 证件号码："+ order.CardID, content_style))
                        story.append(Paragraph("租客电话：" +order.telephone+"&nbsp&nbsp&nbsp" +"租客邮箱"+order.Email, content_style))
                        story.append(Paragraph("保险期间：自北京时间起  "+str(order.start_time)+" 至  "+str(order.end_time)+" 时止", content_style))
                        story.append(Paragraph("支付时间：  "+str(order.OrderDate)+" 约定到账周期： 3 天  支付方式： 银行汇款", content_style))
                        task_table = Table(task_data, colWidths=[75 * mm, 50 * mm, 40 * mm], rowHeights=8 * mm, style=basic_style)
                        story.append(task_table)
                        story.append(Paragraph("总金额： &nbsp&nbsp "+str(order.price)+" 元", content_style))
                        story.append(Paragraph("条款适用： 青年租房管理系统《非金融机构支付服务保险条款》", content_style_line_1))
                        story.append(Paragraph(
                            "<u>_____________________________________________________________________________________________________________________________________________________</u>",
                            content_style_line_1))
                        story.append(Paragraph("特别约定：", content_style))
                        for item in rule:
                            story.append(Paragraph(item, content_style))
                        story.append(Paragraph(
                            "<u>_____________________________________________________________________________________________________________________________________________________</u>",
                            content_style_line_1))
                        story.append(Paragraph('合同争议解决方式： 诉讼 付款方式：趸缴', content_style))
                        doc = SimpleDocTemplate(str(order.OrderID)+".pdf",
                                                leftMargin=20 * mm, rightMargin=20 * mm, topMargin=2 * mm, bottomMargin=20 * mm)
                        doc.build(story)
                        RContract.objects.create(start_time=order.start_time, end_time=order.end_time, price=order.price,userID=order.userID,Email=order.Email,OrderDate=order.OrderDate,HouseID=order.HouseID,CardID=order.CardID,name=order.name,Hname=order.Hname,telephone=order.telephone,OrderID=order.OrderID)                      
                    else:
                        order.OrderState=2
                        order.save()
                    result = {'result': 1, 'message': '租赁成功!'}
                    return JsonResponse(result)     
            else:
                result = {'result': 0, 'message': '房间不存在!'}
                return JsonResponse(result)
    else:
        result = {'result': 0, 'message': '前端炸了!'}
        return JsonResponse(result)
