from django.contrib import admin
from django.core.cache import cache
from apps.goods.models import GoodsType,Goods,GoodsSKU,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner

class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''新增或者更新表中数据时调用'''
        super().save_model(request, obj, form, change)

        cache.delete('index_page_list')
        #发出任务，让celery worker 重新生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        cache.delete('index_page_list')
        # 发出任务，让celery worker 重新生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

# Register your models here.
admin.site.register(GoodsSKU)
admin.site.register(Goods)
admin.site.register(GoodsType)
admin.site.register(IndexGoodsBanner,BaseModelAdmin)
admin.site.register(IndexPromotionBanner,BaseModelAdmin)
admin.site.register(IndexTypeGoodsBanner,BaseModelAdmin)

