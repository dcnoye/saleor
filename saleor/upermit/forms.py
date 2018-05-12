from django import forms

from .models import Technician
from .models import Permit
from .models import Inspection



class PermitForm(forms.ModelForm):
    building_type = forms.CharField(required=True, max_length=6, widget=forms.Select(choices=Permit.BUILDING_TYPE_CHOICES))
    permittee_type = forms.CharField(required=True, max_length=2, widget=forms.Select(choices=Permit.PERMITTEE_TYPE_CHOICES))
    parcel = forms.CharField(required=True, max_length=100)    
  
    job_street_address_1 = forms.CharField(required=True, max_length=100)
    job_street_address_2 = forms.CharField(required=False, max_length=100)
    owner_name = forms.CharField(required=True, max_length=100)
    owner_phone = forms.CharField(required=True, max_length=100)
    subdivision = forms.CharField(required=False, max_length=100)
    lot_block_unit = forms.CharField(required=False, max_length=100)
    sdp_pl = forms.CharField(required=False, max_length=100)
    pl_filename_line1 = forms.CharField(required=False, max_length=100)
    pl_filename_line2 = forms.CharField(required=False, max_length=100)
    
    subcontractors  = forms.CharField(required=False, max_length=100)  # (gas/elec/plumb/mech/roof/septic/lowvoltage/shutters/electfromhouse)
    sub_elec = forms.BooleanField(required=False)
    sub_plumb = forms.BooleanField(required=False)
    sub_mech = forms.BooleanField(required=False)
    sub_roof = forms.BooleanField(required=False)
    sub_septic = forms.BooleanField(required=False)
    sub_lowvoltage = forms.BooleanField(required=False)
    sub_shutters = forms.BooleanField(required=False)
    sub_elecfromhouse = forms.BooleanField(required=False)
    sub_gas = forms.BooleanField(required=False)
    
    related_hurricane_irma = forms.BooleanField(required=False)
    
    project_name = forms.CharField(required=True, max_length=100)
    declared_value = forms.CharField(required=False, max_length=100)
    project_line_1 = forms.CharField(required=False, max_length=100)
    project_line_2 = forms.CharField(required=False, max_length=100)
    project_line_3 = forms.CharField(required=False, max_length=100)
    project_line_4 = forms.CharField(required=False, max_length=100)
    project_line_5 = forms.CharField(required=False, max_length=100)
    
    
    class Meta:
        model = Permit
        fields = ['building_type', 'permittee_type','parcel',
			'job_street_address_1','job_street_address_2',
			'owner_name','owner_phone','subdivision',
			'lot_block_unit','sdp_pl','pl_filename_line1',
			'pl_filename_line2','subcontractors','related_hurricane_irma',
			'project_name','declared_value','project_line_1','project_line_2','project_line_3',
			'project_line_4','project_line_5']
        
        
#        widgets = {
#            'permittee_type': forms.Select(choices=PERMITTEE_TYPE_CHOICES) }
#        widgets = { 
#			'related_hurricane_irma': forms.CheckboxSelectMultiple }
 #           'related_hurricane_irma': forms.BooleanField }
    
    #HouseID = forms.CharField(max_length=100)
    
    
class InspectionForm(forms.ModelForm):
    job_street_address_1 = forms.CharField(required=True, max_length=100)
    job_street_address_2 = forms.CharField(required=False, max_length=100)
    owner_name = forms.CharField(required=True, max_length=100)
    owner_phone = forms.CharField(required=True, max_length=100)
    
    class Meta:
        model = Inspection
        fields = ('job_street_address_1', 'job_street_address_2', 'owner_name', 'owner_phone')
    
    
class TechnicianForm(forms.ModelForm):
    class Meta:
        model = Technician
        fields = ('fullname', 'address', 'phone', 'certificate_photo')
        widgets ={
            'fullname': forms.TextInput(attrs={'class':'form-control'}),
            'address': forms.TextInput(attrs={'class':'form-control'}),
            'phone': forms.TextInput(attrs={'class':'form-control'})}


class ApprovalForm(forms.ModelForm):
    class Meta:
        model = Technician
        fields = ('approved','user')
        widgets ={
            'approved': forms.TextInput(attrs={'class':'form-control'})}
