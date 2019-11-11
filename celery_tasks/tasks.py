from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from celery.utils.log import get_task_logger
from django.template import loader, RequestContext
import os

# import os
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daily.settings')
# django.setup()
app = Celery('celery_tasks.tasks', broker='redis://192.168.137.101:6379/0')
log = get_task_logger(__name__)


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    # 发邮件
    log.info("Calling task add(%s ,%s, %s)" % (to_email, username, token))
    subject = "天天生鲜欢迎信息"
    html_message = "<h1>%s,欢迎您成为天天生鲜注册会员<h1>请点击下面链接激活您的帐户<br/><a href='http://127.0.0.1:8000/user/active/%s'>激活账户</a>" % (
        username, token)
    sender = settings.EMAIL_FROM
    send_mail(subject, '', sender, [to_email], html_message=html_message)


@app.task
def generate_static_index_html():
    """产生首页静态页面"""

	
	 # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
    log.info('Calling promotion_banners %s' %promotion_banners)
    # 获取商品的种类信息
    types = GoodsType.objects.all()
    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')
   
    # 获取首页分类商品展示信息
    for type in types:
        image_goods_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
        font_goods_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)
        type.image_goods_banners = image_goods_banners
        type.font_goods_banners = font_goods_banners

    # 组织上下文
    context = {
        'types': types,
        'goods_banners': goods_banners,
        'promotion_banners': promotion_banners
    }

    # 使用模板
    # 1. 加载模板文件，返回模板对象
    temp = loader.get_template('static_index.html')
    # 2. 渲染模板
    static_index_html = temp.render(context)

    # 生成对应静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(static_index_html)
