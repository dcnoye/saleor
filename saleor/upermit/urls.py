from django.conf.urls import url

from . import views
from .views import TechnicianList

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^technicians/$', TechnicianList.as_view(), name='technicians'),
    url(r'^technicians/new/$', views.new_technician, name='new_technician')]
#    url(r'^technicians-old/', views.technicians_list, name='technicians')]
#    url(r'^shipping-address/', views.shipping_address_view,
#        name='shipping-address'),
#    url(r'^shipping-method/', views.shipping_method_view,
#        name='shipping-method'),
#    url(r'^summary/', views.summary_view, name='summary'),
#    url(r'^remove_voucher/', views.discount.remove_voucher_view,
#        name='remove-voucher'),
#    url(r'^login/', views.login, name='login')]
