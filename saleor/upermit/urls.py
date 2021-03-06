from django.conf.urls import url

from . import views
from .views import TechnicianList
from .views import PermitList

urlpatterns = [
    url(r'^$', PermitList.as_view(), name='index'),
    url(r'^technicians/$', TechnicianList.as_view(), name='technicians'),
    url(r'^technicians/new/$', views.new_technician, name='new_technician'),
    url(r'^permit_form/(?P<id>\d+)/$', views.permit_form, name="permit_form"),
    url(r'^permit_edit/(?P<p_id>\d+)/$', views.permit_edit, name="permit_form"),
    url(r'^technicians/delete/(?P<tech_id>\d+)/$', views.delete_technician, name="tech_form"),
    url(r'^technicians/tech_form/(?P<tech_id>\d+)/$', views.tech_form, name="tech_form"),
    url(r'^permits/$', PermitList.as_view(), name='permits'),
    url(r'^permit_pdf/(?P<id>\d+)/$', views.order_permit_pdf, name='order-permit-pdf'),
    url(r'^inspection_form/(?P<id>\d+)/$', views.inspection_form, name="inspection_form")]
    
#    url(r'^technicians-old/', views.technicians_list, name='technicians')]
#    url(r'^shipping-address/', views.shipping_address_view,
#        name='shipping-address'),
#    url(r'^shipping-method/', views.shipping_method_view,
#        name='shipping-method'),
#    url(r'^summary/', views.summary_view, name='summary'),
#    url(r'^remove_voucher/', views.discount.remove_voucher_view,
#        name='remove-voucher'),
#    url(r'^login/', views.login, name='login')]
