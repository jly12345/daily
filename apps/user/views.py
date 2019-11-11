from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
import re
from apps.user.models import User,Address
from apps.goods.models import GoodsSKU
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.http import HttpResponse
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login,logout
from utils.mixin import LoginRequireMixin
from django_redis import get_redis_connection


class RegisterView(View):
    '''注册'''

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        if not all([username, password, email]):
            return render(request, 'register.html', {'error_msg': '数据不完整'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'error_msg': '邮箱不合法'})

        if allow != 'on':
            return render(request, 'register.html', {'error_msg': '请同意协议'})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'error_msg': '用户已存在'})

        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 发送激活邮件 http://127.0.0.1:8000/user/active/3
        # 激活链接中需要包含用户的身份信息，并且要把身份信息进行加密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()
        send_register_active_email.delay(email, username, token)
        return redirect(reverse('goods:index'))


# def register(request):
#     if request.method == "GET":
#         '''显示注册页面'''
#         return render(request, 'register.html')
#     elif request.method == "POST":
#         username = request.POST.get('user_name')
#         password = request.POST.get('pwd')
#         email = request.POST.get('email')
#         allow = request.POST.get('allow')
#
#         if not all([username, password, email]):
#             return render(request, 'register.html', {'error_msg': '数据不完整'})
#
#         if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#             return render(request, 'register.html', {'error_msg': '邮箱不合法'})
#
#         if allow != 'on':
#             return render(request, 'register.html', {'error_msg': '请同意协议'})
#
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             user = None
#
#         if user:
#             return render(request, 'register.html', {'error_msg': '用户已存在'})
#
#         user = User.objects.create_user(username, email, password)
#         user.is_active = 0
#         user.save()
#         return redirect(reverse('goods:index'))

class ActiveView(View):
    def get(self, request, token):
        print(token)
        # 解密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            userid = info['confirm']
            user = User.objects.get(id=userid)
            user.is_active = 1
            user.save()

            return redirect(reverse("user:login"))
        except SignatureExpired as e:
            return HttpResponse('链接已过期')


class LoginView(View):
    def get(self, request):
        if 'username' in request.COOKIES:
            username = request.COOKIES.get("username")
            checked = 'checked'
        else:
            username = ""
            checked = ""
        return render(request, 'login.html', {"username": username, "checked": checked})

    def post(self, request):
        username = request.POST.get("username")
        pwd = request.POST.get("pwd")
        if not all([username, pwd]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})
        user = authenticate(username=username, password=pwd)
        if user is not None:
            if user.is_active:
                login(request, user)
                remember = request.POST.get("remember")

                next_url =request.GET.get('next',reverse('goods:index'))
                response = redirect(next_url)
                if remember == 'on':
                    response.set_cookie("username", username, 7 * 24 * 3600)
                else:
                    response.delete_cookie("username")
                return response
            else:
                return render(request, 'login.html', {'errmsg': '用户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或者密码错误'})


class UserInfoView(LoginRequireMixin,View):
    '''用户中心-信息页'''

    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user)
        connection = get_redis_connection()
        history_key ='history_%d'%user.id
        sku_ids = connection.lrange(history_key, 0, 4)
        goods_li = GoodsSKU.objects.filter(id__in = sku_ids)
        return render(request, 'user_center_info.html', {'page': 'user','address':address,'user':user,'goods_li':goods_li})


class UserOrderView(LoginRequireMixin,View):
    '''用户中心-订单页'''

    def get(self, request):
        return render(request, 'user_center_order.html', {'page': 'order'})


class AddressView(LoginRequireMixin,View):
    '''用户中心-地址页'''

    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user)
        return render(request, 'user_center_site.html', {'page': 'address','address':address})

    def post(self,request):
        '''地址添加'''
        receiver = request.POST.get('receiver')
        addr = request.POST.get("addr")
        zip_code = request.POST.get("zip_code")
        phone = request.POST.get("phone")

        if not all([receiver,addr,phone]):
            return render(request, 'user_center_site.html', {'page': 'address','errmsg':'信息不全'})
        if not re.match(r'^1(3|4|5|6|7|8|9)\d{9}$',phone):
            return render(request, 'user_center_site.html', {'page': 'address', 'errmsg': '手机格式不正确'})

        user = request.user
        address = Address.objects.get_default_address(user)
        if address:
            is_default=False
        else:
            is_default=True

        Address.objects.create(user=user,addr=addr,receiver=receiver,zip_code=zip_code,phone=phone,is_default=is_default)
        return redirect(reverse("user:address"))


class LogoutView(View):
    '''退出'''
    def get(self,request):
       logout(request)
       return render(request, 'login.html')
