from django import forms

from .models import Technician
from .models import Permit
from .models import Inspection





class PermitForm(forms.ModelForm):
    class Meta:
        model = Permit
        fields = ('building_type', 'permittee_type','parcel',
			'job_street_address_1','job_street_address_2',
			'owner_name','owner_phone','subdivision',
			'lot_block_unit','sdp_pl','pl_filename_line1',
			'pl_filename_line2','subcontractors','related_hurricane_irma',
			'project_name','declared_value','project_line_2','project_line_3',
			'project_line_4','project_line_5'
        )
        widgets = { 
			'related_hurricane_irma': forms.CheckBoxInput }
    
    HouseID = forms.CharField(max_length=100)
    
    
class InspectionForm(forms.ModelForm):
    inspect_address = forms.CharField(max_length=100)
    
    
class TechnicianForm(forms.ModelForm):
    class Meta:
        model = Technician
        fields = ('fullname', 'address', 'phone', 'certificate_photo')
        widgets ={
            'fullname': forms.TextInput(attrs={'class':'form-control'}),
            'address': forms.TextInput(attrs={'class':'form-control'}),
            'phone': forms.TextInput(attrs={'class':'form-control'})}
            
            
