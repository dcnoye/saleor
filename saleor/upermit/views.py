from django.forms import modelformset_factory
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, permission_required
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
from .forms import ApprovalForm

import datetime
import logging

logger = logging.getLogger(__name__)

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
            #return TemplateResponse(request, 'upermit/technician_list.html', {'technician': tech})
            return redirect('upermit:technicians')
    else:
        form = TechnicianForm()
        
    return TemplateResponse(request, 'upermit/new_technician.html', {'form': form })

@staff_member_required
@permission_required('account.edit_staff')
def delete_technician(request, tech_id):
    tech = Technician.objects.get(id = tech_id)
    tech.delete()
    return redirect('upermit:technicians')


def tech_form(request, tech_id):
    tech = Technician.objects.get(id = tech_id)
    if tech.approved == 0:
        tech.approved = 1
        tech.save()
        return redirect('upermit:technicians')
    else:
        tech.approved = 0
        tech.save()
        return redirect('upermit:technicians')


def permit_form(request, id):
    #permit = Permit.objects.prefetch_related('lines');
    permitx = Permit.objects.get(id = id) 
        
    if request.method == 'POST':
        
        form = PermitForm(request.POST)
        current_user = request.user
        # create a form instance and populate it with data from the request:
        # check whether it's valid:
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user_id = current_user.id
            obj.order_id = id
            obj.save()
            return TemplateResponse(request, 'upermit/index.html')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = PermitForm(instance=permitx)
    
    return TemplateResponse(request, 'upermit/permit_form.html', {'form': form })   

    
def inspection_form(request, id):
    #permit = Permit.objects.prefetch_related('lines');
    
    # Test to see if the user is anonymous or not - i.e. only allow registered users
    # to touch this.
    if not request.user.is_authenticated:
        response = HttpResponse("")
        return response

        
    if request.method == 'POST':
        
        current_user = request.user
        # create a form instance and populate it with data from the request:
        #form = PermitForm(request.POST)
        # check whether it's valid:
        #if form.is_valid():
        #    obj = form.save(commit=False)
        #    obj.user_id = current_user.id
        #    obj.order_id = 11
        """
        retstr=""
        for attr in dir(obj.order_id):
            if hasattr( obj.order_id, attr ):
                retstr = retstr + str((attr, getattr(obj.order_id, attr)))
        response = HttpResponse(retstr)
        return response
        """
        #    obj.save()
        #    return TemplateResponse(request, 'upermit/index.html')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = InspectionForm()
    
    return TemplateResponse(request, 'upermit/inspection_form.html', {'form': form })    
        
def permit_confirm(request):
    if not request.user.is_authenticated:
        response = HttpResponse("")
        return response

    if request.method == 'POST':
        
        current_user = request.user
        # create a form instance and populate it with data from the request:
        form = PermitForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            retstr=""
            for attr in dir(form):
                if hasattr( form, attr ):
                    retstr = retstr + str((attr, getattr(form, attr)))
            response = HttpResponse(retstr)
            return response
            
            return TemplateResponse(request, 'upermit/permit_confirm.html', {'form': form})
        else:
            return TemplateResponse(request, 'upermit/technician_list.html')

def permit_edit(request,p_id):
    if not request.user.is_authenticated:
        response = HttpResponse("")
        return response

    if request.method == 'POST':

        current_user = request.user
        # create a form instance and populate it with data from the request:
        form = PermitForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            retstr=""
            for attr in dir(form):
                if hasattr( form, attr ):
                    retstr = retstr + str((attr, getattr(form, attr)))
            response = HttpResponse(retstr)
            return response

            return TemplateResponse(request, 'upermit/permit_confirm.html', {'form': form})
        else:
            return TemplateResponse(request, 'upermit/technician_list.html')


class TechnicianList(ListView):
    model = Technician
    template_name = 'upermit/technician_list.html'
    context_object_name = 'technicians'
    
    def get_queryset(self):
        #tech_list = Technician.objects.filter(user=self.request.user)
        tech_list = list(Technician.objects.all())
        return tech_list
        
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TechnicianList, self).dispatch(*args, **kwargs)        
    

class PermitList(ListView):
    model = Permit
    template_name = 'upermit/index.html'
    context_object_name = 'permits'
    
#   def get_queryset(self):
#       permit_list = Permit.objects.filter(user=self.request.user)
#       return permit_list
    logger.debug("PERMIT LIST PERMIT LIST PERMIT LIST PERMIT LIST PERMIT LIST PERMIT LIST PERMIT LIST PERMIT LIST PERMIT LIST PERMIT LIST ")
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PermitList, self).dispatch(*args, **kwargs)        
    
#@staff_member_required
#@permission_required('order.edit_order')
def order_permit_pdf(request, id):
#    orders = Order.objects.prefetch_related(
#        'user', 'shipping_address', 'billing_address', 'voucher')
#    order = get_object_or_404(orders, pk=order_pk)
#    absolute_url = get_statics_absolute_url(request)

#    rendered_template = get_template(INVOICE_TEMPLATE).render(ctx)
    
    # Test to see if the user is anonymous or not - i.e. only allow registered users
    # to touch this.
    if not request.user.is_authenticated:
        response = HttpResponse("")
        return response
        
    permit = Permit.objects.get(id=id)

#    for name in vars().keys():
#        print(name)
  
#    for value in vars().values():
#        print(value)  

    from PyPDF2 import PdfFileWriter, PdfFileReader
    import io
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    packet = io.BytesIO()

    # create a new PDF with Reportlab - and fill in all the data.
    can = canvas.Canvas(packet, pagesize=letter)

    # Default font
    can.setFont("Times-Roman", 11)

#------------
# For debugging purposes.
#
    """
    i=700
    for attr in dir(permit.when_created.day):
        if hasattr( permit.when_created.day, attr ):
            can.drawString(10, i, "permit.%s = %s" % (attr, getattr(permit.when_created.day, attr)))
            i=i-5
    """

#--------------------
# Handle time/date formats here.
# order.created = 2018-04-22 20:17:35.283285+00:00

#--------------------
# Start populating the checkboxes (page 1)

    can.setFont("Times-Roman", 18)
    
    #can.drawString(10, 700, "%s = %s" % (attr, getattr( ).toString())
    
    # Permittee type

    # Contractor
    #can.drawString(155, 604, "X")
    if (findWholeWord('CO')(permit.permittee_type)):
    #if 'CO' in permit.permittee_type:
        can.drawString(155, 604, "X")

    # Design Professional
    if (findWholeWord('DP')(permit.permittee_type)):
    #if 'DP' in permit.permittee_type:
        can.drawString(303, 604, "X")

    # Owner Builder
    if (findWholeWord('OB')(permit.permittee_type)):
        can.drawString(485, 604, "X")


    # Building type
    
    # 1 & 2 Family Dwelling / Townhouse
    if (findWholeWord('ONETWO')(permit.building_type)):
        can.drawString(141, 623, "X")

    # Mobile/Manufactured home
    if (findWholeWord('MOBMAN')(permit.building_type)):    
        can.drawString(270, 623, "X")


    # Residential 3+ units/Multi-family
    if (findWholeWord('RS3MLT')(permit.building_type)):    
        can.drawString(388, 623, "X")

    # Commercial
    if (findWholeWord('COMMER')(permit.building_type)):    
        can.drawString(523, 623, "X")



#-------------------------------
# Start populating the Property Information (page 1)

    # Reset the font in case it was changed elsewhere
    can.setFont("Times-Roman", 11)

    # Those are 13 y units apart
    #can.drawString(120, 574, "Parcel/Folio Line 1234567890")
    can.drawString(120, 574, permit.parcel)

#    can.drawString(120, 561, order.billing_address.street_address_1)
#    can.drawString(120, 561, "Address Line 1 12345678901234567890")
#    can.drawString(120, 548, "Address Line 2 12345678901234567890")
    if (permit.job_street_address_1):
        can.drawString(120, 561, permit.job_street_address_1)
    
    if (permit.job_street_address_2):
        can.drawString(120, 548, permit.job_street_address_2)
    
    
#    can.drawString(120, 561,     for name in vars().keys():
#        print(name)


#    addr2=order.billing_address.street_address_2 + " " + order.billing_address.city + ", " + order.billing_address.country_area + " " + order.billing_address.postal_code


    #can.drawString(120, 548, addr2)
#

    # 14 units..
 #   can.drawString(120, 534, order.billing_address.full_name) # Owner name
    if (permit.owner_name):
        can.drawString(120, 534, permit.owner_name) # Owner name

    # 13 units
  #  can.drawString(120, 521, order.billing_address.phone.as_national) # Owner phone
    if (permit.owner_phone):
        can.drawString(120, 521, permit.owner_phone) # Owner phone

    if (permit.subdivision):
        can.drawString(120, 508, permit.subdivision)
    
    # etc. 
    if (permit.lot_block_unit):
        can.drawString(120, 494, permit.lot_block_unit)
        
    if (permit.sdp_pl):
        can.drawString(120, 481, permit.sdp_pl)
        
    if (permit.pl_filename_line1):
        can.drawString(120, 468, permit.pl_filename_line1)
        
    if (permit.pl_filename_line2): 
        can.drawString(120, 455, permit.pl_filename_line2)


#-----------------------
# Start populating application information
    can.setFont("Times-Roman", 16)

    # Sub contractors.
    # Elec
    if (findWholeWord('ELEC')(permit.subcontractors)):    
        can.drawString(120, 410, "X")

    # Plumb
    if (findWholeWord('PLUMB')(permit.subcontractors)):    
        can.drawString(157, 410, "X")

    # Mech
    if (findWholeWord('MECH')(permit.subcontractors)):    
        can.drawString(208, 410, "X")

    # Roof
    if (findWholeWord('ROOF')(permit.subcontractors)):    
        can.drawString(256, 410, "X")

    # Septic
    if (findWholeWord('SEPTIC')(permit.subcontractors)):    
        can.drawString(299, 410, "X")

    # Low Voltage
    if (findWholeWord('LOWVOLTAGE')(permit.subcontractors)):    
        can.drawString(342, 410, "X")

    # Shutters
    if (findWholeWord('SHUTTERS')(permit.subcontractors)):    
        can.drawString(407, 410, "X")

    # ELECT from house
    if (findWholeWord('ELECFROMHOUSE')(permit.subcontractors)):    
        can.drawString(455, 410, "X")

    # Gas
    if (findWholeWord('GAS')(permit.subcontractors)):    
        can.drawString(540, 410, "X")

    if (permit.related_hurricane_irma == "false"):
        can.drawString(553, 335, "X")
    else:
        can.drawString(518, 335, "X")
    
    # Related to Hurricane Irma
    # No
    #can.drawString(553, 335, "X")
    # Yes
    #can.drawString(518, 335, "X")


#----------------------
# Start populating project information

    # Reset the font in case it was changed elsewhere
    can.setFont("Times-Roman", 11)

    # Project name
    if (permit.project_name):
        can.drawString(278, 303, permit.project_name)

    # Declared Value
    if (permit.declared_value):
        can.drawString(504, 303, permit.declared_value)

    # Line 1
    if (permit.project_line_1):
        can.drawString(23, 288, permit.project_line_1)

    # Line 2
    if (permit.project_line_2):
        can.drawString(23, 274, permit.project_line_2)

    # Line 3
    if (permit.project_line_3):
        can.drawString(23, 260, permit.project_line_3)

    # Line 4
    if (permit.project_line_4):
        can.drawString(23, 246, permit.project_line_4)

    # Line 5
    if (permit.project_line_5):
        can.drawString(23, 232, permit.project_line_5)


#-----------------------
# Start a new page.
    can.showPage()

    #can.drawString(282,452,"01")
    # Section A
    can.drawString(282,452,str(permit.when_created.day))            # Day
    can.drawString(353,452,permit.when_created.strftime("%B"))      # Month
    can.drawString(462,452,str(permit.when_created.year - 2000))    # Year

    #    can.drawString(282,452,order.created.strftime("%d"))     # Day
    #    can.drawString(353,452,order.created.strftime("%B"))  # Month
    #    can.drawString(462,452,order.created.strftime("%y"))   # Year



    # Section B
    can.drawString(282,325,str(permit.when_created.day))            # Day
    can.drawString(353,325,permit.when_created.strftime("%B"))      # Month
    can.drawString(462,325,str(permit.when_created.year - 2000))    # Year

    #    can.drawString(282,325,order.created.strftime("%d"))     # Day
    #    can.drawString(353,325,order.created.strftime("%B"))  # Month
    #    can.drawString(462,325,order.created.strftime("%y"))   # Year


#-----------------------
# End of entering data into the form.
#

    # Save it.
    can.save()

#    from subprocess import call
#    call(["pwd", ""])

    # move to the beginning of the StringIO buffer
    packet.seek(0)
    new_pdf = PdfFileReader(packet)

    # read your existing PDF
    existing_pdf = PdfFileReader(open("/var/www/saleor/template_0001.pdf", "rb"))

    # Rotate it counter-clockwise
#    existing_pdf.getPage(0).rotateCounterClockwise(2)
    # Figure out how to rotate it later on. 

    output = PdfFileWriter()

    # debug 
#    page0 = new_pdf.getPage(0)
#    output.addPage(page0)
    # end debug

    page = existing_pdf.getPage(0)
    page.mergePage(new_pdf.getPage(0)) # 0 normal, 1 debug
    output.addPage(page)

    # add the second page.
    page2 = existing_pdf.getPage(1)
    output.addPage(page2)

    # Now add in the third page.
    page3 = existing_pdf.getPage(2)
    page3.mergePage(new_pdf.getPage(1)) # 1 normal, 2 debug
    output.addPage(page3)


#---------------------------
# Now write out the pdf data.
    bytesOut = io.BytesIO()
    output.write(bytesOut)
    bytesOut.seek(0)

#    pdf_file, order = create_invoice_pdf(order, absolute_url)

    response = HttpResponse(bytesOut, content_type='application/pdf')
    #name = "permit-%s" % order.id
    name = "permit-0"
    response['Content-Disposition'] = 'filename=%s' % name
    return response


# From https://stackoverflow.com/questions/5319922/python-check-if-word-is-in-a-string
import re

def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

