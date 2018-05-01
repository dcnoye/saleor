from django import forms

from .models import Technician
from .models import Permit
from .models import Inspection





class PermitForm(forms.ModelForm):
    class Meta:
        model = Permit
        fields = ()
        widgets = { }
    
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
            
            
