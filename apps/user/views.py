from django.shortcuts import render, redirect
from django.urls import reverse
import re
from apps.user.models import User


def register(request):
    if request.method == "GET":
        '''显示注册页面'''
        return render(request, 'register.html')
    elif request.method == "POST":
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
        return redirect(reverse('goods:index'))
