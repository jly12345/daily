from django.db import models
from db.base_model import BaseModel

class OrderInfo(BaseModel):
    '''订单模型'''
    PAY_METHOD_CHOICES=((1,'货到付款'),(2,'微信支付'),(3,'支付宝支付'),(4,'银联支付'))
    ORDER_STATUS_CHOICES=((1,'待支付'),(2,'待发货'),(3,'待收货'),(4,'待评价'),(5,'已完成'))

    order_id=models.CharField(max_length=128,primary_key=True,verbose_name='订单Id')
    user=models.ForeignKey('user.User',on_delete=models.CASCADE,verbose_name='用户')
    pay_method=models.SmallIntegerField(choices=PAY_METHOD_CHOICES,default=3,verbose_name='支付方式')
    total_count=models.IntegerField(default=1,verbose_name='商品总数量')
    total_price=models.DecimalField(max_digits=10,decimal_places=2,verbose_name='商品总价格')
    transit_price=models.DecimalField(max_digits=10,decimal_places=2,verbose_name='商品总价格')
    order_status=models.SmallIntegerField(choices=ORDER_STATUS_CHOICES,default=1,verbose_name='商品总价格')
    tran_no=models.CharField(max_length=128,verbose_name='支付编号')

    class Meta:
        db_table = 'df_order_info'
        verbose_name = '订单'
        verbose_name_plural = verbose_name

class OrderGoods(BaseModel):
    '''订单商品'''
    order=models.ForeignKey('OrderInfo',on_delete=models.CASCADE,verbose_name='订单')
    sku=models.ForeignKey('goods.GoodsSKU',on_delete=models.CASCADE,verbose_name='商品SKU')
    count=models.IntegerField(default=1,verbose_name='商品数量')
    price=models.DecimalField(max_digits=10,decimal_places=2,verbose_name='商品价格')
    comment=models.CharField(max_length=256,verbose_name='评论')

    class Meta:
        db_table = 'df_order_goods'
        verbose_name = '订单商品'
        verbose_name_plural = verbose_name