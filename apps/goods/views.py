from django.shortcuts import render,redirect,reverse
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner,GoodsSKU

from apps.order.models import OrderGoods
from django.views.generic import View
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.paginator import Paginator

class IndexView(View):
    def get(self, request):
        '''首页'''

        context = cache.get("index_page_list")
        if context is None:
            # 获取商品的种类信息
            types = GoodsType.objects.all()
            # 获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')
            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
            # 获取首页分类商品展示信息
            for type in types:
                image_goods_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
                font_goods_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)
                type.image_goods_banners = image_goods_banners
                type.font_goods_banners = font_goods_banners

            context = {
                'types': types,
                'goods_banners': goods_banners,
                'promotion_banners': promotion_banners
            }
            #设置缓存
            cache.set("index_page_list",context,3600)
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            connection = get_redis_connection("default")
            cart_key = "cart_%d" % user.id
            cart_count = connection.hlen(cart_key)
        # 组织上下文
        context.update(cart_count=cart_count)
        return render(request, 'index.html', context)
        # #使用模板
        # #加载模板文件
        # template = loader.get_template("static_index.html")
        # #定义模板上下文
        # context = RequestContext(request, context)
        # static_index_html = template.render(context)
        # #生成首页静态页面
        # save_path =os.path.join(settings.BASE_DIR,"static/index.html")
        # with open(save_path,'w') as f:
        #     f.write(static_index_html)
# Create your views here.

class DetailView(View):
    def get(self,request,id):
        #商品分类信息
        types = GoodsType.objects.all()
        #商品详情
        try:
            sku = GoodsSKU.objects.get(id=id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse("goods:index"))

        #商品评论
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        #获取新品信息
        search_dict = dict()
        search_dict['type']=sku.type
        search_dict['is_delete']=False
        newGoods = GoodsSKU.objects.filter(**search_dict).order_by("-create_time")[:2]
        # newGoods = GoodsSKU.objects.filter(type=sku.type).order_by("-create_time")
        #获取同一个SPU的其他规格商品
        same_spu_skus = GoodsSKU.objects.filter(type=sku.type).exclude(id=id)
        context = {
            'types': types,
            'sku_orders': sku_orders,
            'sku': sku,
            'newGoods': newGoods,
            'same_spu_skus': same_spu_skus
        }
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            connection = get_redis_connection("default")
            cart_key = "cart_%d" % user.id
            cart_count = connection.hlen(cart_key)

            connection = get_redis_connection("default")
            history_key = "history_%d" % user.id
            connection.lrem(history_key,0,id)
            connection.lpush(history_key,id)
            connection.ltrim(history_key,0,4)
        # 组织上下文
        context.update(cart_count=cart_count)
        return render(request,'detail.html',context)


class ListView(View):
    def get(self,request,type_id,page):
        try:
            type = GoodsType.objects.filter(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse("goods:index"))
        sort= request.GET.get('sort')
        if sort =='price':
            skus = GoodsSKU.objects.filter(type=type).order_by("price")
        elif sort =='hot':
            skus = GoodsSKU.objects.filter(type=type).order_by("-sales")
        else:
            skus = GoodsSKU.objects.filter(type=type).order_by("-id")

        #分页
        paginator = Paginator(skus, 1)

        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page> paginator.num_pages:
            page =1
        #获取第page页的Page实例对象
        skus_page = paginator.page(page)

        #获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type_id).order_by('-create_time')[:2]
        types = GoodsSKU.objects.all()

        #获取购物车商品数目
        user = request.user
        if user.is_authenticated():
            connection = get_redis_connection("default")
            cart_key = "cart_%d" % user.id
            cart_count = connection.hlen(cart_key)
        context = {
            'types': types,
            'skus': skus,
            'cart_count':cart_count,
            'new_skus':new_skus,
            'skus_page':skus_page,
            'type_id':type_id,
            'sort':sort,
        }
        return render(request,'list.html',context)
