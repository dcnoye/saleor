from django.conf import settings
from django.contrib.admin.views.decorators import (
    staff_member_required as _staff_member_required, user_passes_test)
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.db.models import Q, Sum
from django.template.response import TemplateResponse
from payments import PaymentStatus
from django.shortcuts import get_object_or_404, redirect, render

from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from ..order import OrderStatus
from ..order.models import Order, Payment
from ..product.models import Product

from django.http import HttpResponse, HttpResponseRedirect

from .models import Technician
from .models import Permit
from .models import Inspection

from .forms import TechnicianForm
from .forms import PermitForm
from .forms import InspectionForm

def staff_member_required(f):
    return _staff_member_required(f, login_url='account:login')


def superuser_required(
        view_func=None, redirect_field_name=REDIRECT_FIELD_NAME,
        login_url='account:login'):
    """Check if the user is logged in and is a superuser.

    Otherwise redirects to the login page.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator

""" 
By default, if anybody goes to the upermit page, index gets called.

But since we have technicians operating out of the same path (upermit).. 
It makes sense to have index for "past orders" and have technician's index
be seperate. 
"""

"""
def index(request):
    #permit = Permit.objects.prefetch_related('lines')
    permit = Permit.objects.all()
    
    # Test to see if the user is anonymous or not - i.e. only allow registered users
    # to touch this.
    if not request.user.is_authenticated:
        response = HttpResponse("")
        return response
        
    form = PermitForm()
    
    return TemplateResponse(request, 'upermit/index.html', {'permit': permit} )
"""
    

def technicians_list(request):
	"""
	technicians = Technician.objects.prefetch_related(
		'user')
		
	technicians = technicians.select_related(
		'user')
	
	tech = get_object_or_404(technicians)
	"""
	
	tech = Technician.objects.prefetch_related('lines');
	
	ctx = {'technician': tech}
	return TemplateResponse(request, 'upermit/technician_list.html', ctx)


@staff_member_required
def styleguide(request):
    return TemplateResponse(request, 'dashboard/styleguide/index.html', {})



def new_technician(request):
	
	# Test to see if the user is anonymous or not - i.e. only allow registered users
	# to touch this.
	if not request.user.is_authenticated:
		response = HttpResponse("")
		return response
		
	
	
	
	
	#if request.method == 'POST' and request.FILES['certificate_photo']:
		
	if request.method == 'POST':
		current_user = request.user
		
		
		form = TechnicianForm(request.POST, request.FILES)
		if form.is_valid():
			obj = form.save(commit=False)
			obj.user_id = current_user.id
			form.save()

			tech = Technician.objects.prefetch_related('lines');
			return TemplateResponse(request, 'upermit/technician_list.html', {'technician': tech})
	else:
		form = TechnicianForm()
		
	return TemplateResponse(request, 'upermit/new_technician.html', {'form': form })


def permit_form(request):
    #permit = Permit.objects.prefetch_related('lines');
    
    # Test to see if the user is anonymous or not - i.e. only allow registered users
    # to touch this.
    if not request.user.is_authenticated:
        response = HttpResponse("")
        return response
        
        
    if request.method == 'POST':
        current_user = request.user
        # create a form instance and populate it with data from the request:
        form = PermitForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user_id = current_user.id
            form.save()
            return TemplateResponse(request, 'upermit/index.html')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = PermitForm()
	
    return TemplateResponse(request, 'upermit/permit_form.html', {'form': form })    
    

class TechnicianList(ListView):
	model = Technician
	template_name = 'upermit/technician_list.html'
	context_object_name = 'technicians'
	
	def get_queryset(self):
		tech_list = Technician.objects.filter(user=self.request.user)
		return tech_list
		
	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(TechnicianList, self).dispatch(*args, **kwargs)		
	

class PermitList(ListView):
	model = Permit
	template_name = 'upermit/index.html'
	context_object_name = 'permits'
	
#	def get_queryset(self):
#		permit_list = Permit.objects.filter(user=self.request.user)
#		return permit_list
		
	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(PermitList, self).dispatch(*args, **kwargs)		
	
