from django.db import models
from django.contrib.auth.models import User
from django.db.models.base import Model
from django.db.models.deletion import PROTECT
from .storage import *
# Create your models here.


class UserInfo(models.Model):
    userID = models.IntegerField(primary_key=True, verbose_name='用户ID')
    email = models.EmailField(verbose_name='邮箱', blank=False)
    username = models.CharField(max_length=25, null=True, verbose_name='用户名')
    password = models.CharField(max_length=50, verbose_name='密码')
    role = models.IntegerField(
        default=2, blank=True, null=True, verbose_name='用户角色')  # 1为管理员，2为租户，3为师傅
    sex = models.IntegerField(blank=True, null=True, verbose_name='性别')  # 1为男士，2为女士
    age = models.IntegerField(blank=True, null=True, verbose_name='年龄')
    header = models.ImageField(
        blank=True,null=True, verbose_name='头像', upload_to='avatars/%Y%m%d',storage=ImageStorage())
    money = models.IntegerField(default=0, verbose_name='钱包')
    telephone = models.CharField(max_length=25, null=True, verbose_name='租客电话')
    birth=models.CharField(max_length=25, null=True, verbose_name='生日')
    summary=models.CharField(max_length=100, null=True, verbose_name='个人资料')
    CardID = models.CharField(max_length=25, null=True, verbose_name='租客身份证号')

    class Meta:
        db_table = "UserInfo"

    @property
    def get_photo_url(self):
        if self.header and hasattr(self.header, 'url'):
            return 'http://43.138.77.8/dz/roomhubSite'+self.header.url
        else:
            return "https://z3.ax1x.com/2021/06/09/2cTNY4.png"


class RContract(models.Model):
    ContractID = models.AutoField(primary_key=True, verbose_name='合同ID')
    start_time = models.DateField(blank=True, null=True, verbose_name='开始日期')
    end_time = models.DateField(blank=True, null=True, verbose_name='结束日期')
    price = models.IntegerField(blank=True, null=True, verbose_name='租金')
    userID = models.IntegerField(blank=True, null=True, verbose_name='租客id')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True, null=True)
    OrderDate = models.DateTimeField(
        auto_now_add=True, null=True, verbose_name='下单时间')
    HouseID = models.IntegerField(verbose_name='房间ID')
    Email = models.EmailField(verbose_name='邮箱', blank=True)
    CardID = models.CharField(max_length=25, null=True, verbose_name='租客身份证号')
    name = models.CharField(max_length=25, null=True, verbose_name='租客姓名')
    Hname = models.CharField(max_length=25, null=True, verbose_name='房间名')
    telephone = models.CharField(max_length=25, null=True, verbose_name='租客电话')
    OrderID = models.IntegerField(blank=True, null=True,verbose_name='订单ID')
    contract = models.FileField(verbose_name='合同', upload_to='contract/%Y%m%d', storage=FileStorage(),blank=True, null=True)
    

    class Meta:
        managed = True
        db_table = 'R_contract'
        verbose_name_plural = '合同管理'

    def __str__(self):
        return str(self.start_time)


class RCollect(models.Model):
    CollectID = models.AutoField(primary_key=True, verbose_name='收藏ID')
    userID = models.IntegerField()
    HouseID = models.IntegerField()


class RHouse(models.Model):
    HouseID = models.IntegerField(primary_key=True, verbose_name='房间ID')
    name = models.CharField(max_length=1000, blank=True,
                            null=True, verbose_name='房屋名称')
    address = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='房屋地址')
    price = models.IntegerField(blank=True, null=True, verbose_name='房屋租金')
    house_size = models.IntegerField(
        blank=True, null=True, verbose_name='房屋面积')
    status = models.CharField(max_length=25, verbose_name='房屋状态')  # 正常出售，暂定出售
    category = models.CharField(max_length=25,verbose_name='房屋类型')  # 单人间，双人间，四人间
    type = models.CharField(max_length=25, verbose_name='租赁类型')  # 长租，短租
    is_near_subway = models.IntegerField(
        default=2, verbose_name='是否近地铁')  # 1为有，0为没有
    is_has_dw = models.IntegerField(
        default=2, verbose_name='是否有独卫')  # 1为有，0为没有
    is_has_yt = models.IntegerField(
        default=2, verbose_name='是否有阳台')  # 1为有，0为没有
    total_views = models.PositiveIntegerField(default=0, verbose_name='浏览量')
    style = models.CharField(max_length=200,null=True, verbose_name='风格')
    summary = models.CharField(max_length=200,null=True, verbose_name='概要')
    rules = models.CharField(max_length=200,null=True, verbose_name='房屋守则')
    bed = models.IntegerField(null=True, verbose_name='床数')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    update_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        managed = True
        db_table = 'House'
        verbose_name_plural = '房屋管理'

    def __str__(self):
        return self.name


class RImg(models.Model):
    imgid = models.AutoField(primary_key=True)
    HouseID = models.IntegerField(blank=True)
    img = models.ImageField(blank=True,upload_to='image/%Y%m%d',storage=ImageStorage())


class Order(models.Model):
    """
    订单表
    """
    OrderID = models.AutoField(primary_key=True, verbose_name='订单ID')
    OrderDate = models.DateTimeField(
        auto_now_add=True, null=True, verbose_name='下单时间')
    HouseID = models.IntegerField(verbose_name='房间ID')
    userID = models.IntegerField(verbose_name='用户ID')
    Email = models.EmailField(verbose_name='邮箱', blank=True)
    OrderState = models.IntegerField(
        default=0, verbose_name='订单状态')   # 1为待审核，2为已通过审核未支付，3未通过审核 4为已通过审核已支付 5待签订
    CardID = models.CharField(max_length=25, null=True, verbose_name='租客身份证号')
    name = models.CharField(max_length=25, null=True, verbose_name='租客姓名')
    Hname = models.CharField(max_length=25, null=True, verbose_name='房间名')
    telephone = models.CharField(max_length=25, null=True, verbose_name='租客电话')
    start_time = models.DateField(blank=True, null=True, verbose_name='开始日期')
    end_time = models.DateField(blank=True, null=True, verbose_name='结束日期')
    price = models.IntegerField(blank=True, null=True, verbose_name='租金')
    see = models.IntegerField(blank=True, null=True, verbose_name='是否可见') #1可见，0不可见
    reason = models.CharField(max_length=25, null=True, verbose_name='审核结果')
    month = models.IntegerField(max_length=25, blank=True,null=True, verbose_name='月份')
    overtime = models.IntegerField(max_length=25, blank=True,null=True, verbose_name='逾期')
    cnt = models.IntegerField(max_length=25, default=0,verbose_name='次数')
    class Meta:
        db_table = "Order"


class Repair(models.Model):
    RepairID = models.AutoField(primary_key=True,verbose_name='维修ID')
    HouseID = models.IntegerField(verbose_name='房间ID')
    userID = models.IntegerField(verbose_name='用户ID')
    picture = models.ImageField(
        verbose_name='照片', upload_to='repair/%Y%m%d',storage=ImageStorage(), blank=True, null=True)
    description = models.TextField(verbose_name='描述', default='', null=True)
    done = models.IntegerField(verbose_name='是否已处理')  #1.待安排，2.维修中，3.待评价，4.已完成
    operatorID = models.IntegerField(verbose_name='维修者', null=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    reply = models.TextField(verbose_name='回复', default='', null=True)
    comment = models.IntegerField(verbose_name='评价', default=0, null=True) #分数范围0-5
    address = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='房屋地址')
    telephone = models.CharField(max_length=25, null=True, verbose_name='租客电话')
    repair_time = models.CharField(max_length=25,null=True, verbose_name='维修时间')
    re_picture = models.ImageField(verbose_name='回复图片', upload_to='re_repair/%Y%m%d',storage=ImageStorage(), blank=True, null=True)
    class Meta:
        db_table = "Repair"
        verbose_name_plural = '报修'
    
    @property
    def get_photo_url(self):
        if self.picture and hasattr(self.picture, 'url'):
            return 'http://43.138.77.8/dz/roomhubSite'+self.picture.url
        else:
            return "https://z3.ax1x.com/2021/06/09/2cqBCD.png"

    @property
    def get_operatorID(self):
        if self.operatorID :
            return self.operatorID 
        else:
            return -1

    @property
    def get_re_photo_url(self):
        if self.re_picture and hasattr(self.re_picture, 'url'):
            return 'http://43.138.77.8/dz/roomhubSite'+self.re_picture.url
        else:
            return "https://z3.ax1x.com/2021/06/09/2cqBCD.png"

class Complaint(models.Model):
    ComplaintID = models.AutoField(primary_key=True, verbose_name='投诉ID')
    HouseID = models.IntegerField(verbose_name='房间ID')
    userID = models.IntegerField(verbose_name='用户ID')
    picture = models.ImageField(
        verbose_name='照片', upload_to='complaint/%Y%m%d',storage=ImageStorage(), blank=True, null=True)
    description = models.TextField(verbose_name='描述', default='', null=True)
    done = models.IntegerField(verbose_name='是否已处理')  #1待处理 2已完成
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    reply = models.TextField(verbose_name='回复', default='', null=True)
    address = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='房屋地址')
    telephone = models.CharField(max_length=25, null=True, verbose_name='租客电话')

    class Meta:
        db_table = "Complaint"
        verbose_name_plural = '投诉'

    @property
    def get_photo_url(self):
        if self.picture and hasattr(self.picture, 'url'):
            return 'http://43.138.77.8/dz/roomhubSite'+self.picture.url
        else:
            return "https://z3.ax1x.com/2021/06/09/2cqBCD.png"


class EmailCode(models.Model):
    code = models.CharField(max_length = 50)
    time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)



