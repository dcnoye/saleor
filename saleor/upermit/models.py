from django.conf import settings
from django.db import models


class Technician(models.Model):
	fullname = models.CharField(
		max_length=100)
		
	address = models.CharField(
		max_length=100)
		
	phone = models.CharField(
		max_length=100)

	approved = models.CharField(
		max_length=1,
		default=0)

	certificate_photo = models.ImageField(upload_to='images/%m/%d')
	
	user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='technicians',
        on_delete=models.SET_NULL)
	
	datetime_created = models.DateTimeField(
		auto_now_add=True, editable=False)


	class Meta:
		verbose_name_plural = 'technicians'
		
"""	def __unicode__(self)
		return u"%s's Technician Info" %self.user_id"""
		
		
    		
class Permit(models.Model):
#    building_type = models.CharField(max_length=100) # (1_2_family_townhouse, mobile_manu, res_3_multifam, commercial)
    ONE_TWO_FAMILY_TOWNHOUSE = 'ONETWO'
    MOBILE_MANU = 'MOBMAN'
    RES_3_MULTIFAM = 'RS3MLT'
    COMMERCIAL = 'COMMER'
    
    BUILDING_TYPE_CHOICES = (
        (ONE_TWO_FAMILY_TOWNHOUSE, '1 and 2 Family dwelling Townhouse'),
        (MOBILE_MANU, 'Mobile Manufactured home'),
        (RES_3_MULTIFAM, 'Residential 3 units Multi family'),
        (COMMERCIAL, 'Commercial')
    )
    
    CONTRACTOR = 'CO'
    DESIGN_PRO = 'DP'
    OWNER_BUILDER = 'OB'

    PERMITTEE_TYPE_CHOICES = (
		(CONTRACTOR, 'Contractor'),
		(DESIGN_PRO, 'Design Professional'),
		(OWNER_BUILDER, 'Owner Builder'),
	)
    
    
    building_type = models.CharField(
        max_length=6,
        choices=BUILDING_TYPE_CHOICES,
        default=ONE_TWO_FAMILY_TOWNHOUSE
    )

    permittee_type = models.CharField(
        max_length=2,
        choices=PERMITTEE_TYPE_CHOICES,
        default=CONTRACTOR
    )
    
    #permittee_type = models.CharField(max_length=100) # (contractor/designpro/ownerbuilder
    
    parcel = models.CharField(max_length=100) 
    job_street_address_1 = models.CharField(max_length=45) 
    job_street_address_2 = models.CharField(max_length=45) 
    owner_name = models.CharField(max_length=100) 
    owner_phone = models.CharField(max_length=100) 
    subdivision = models.CharField(max_length=100) 
    lot_block_unit = models.CharField(max_length=100) 
    sdp_pl = models.CharField(max_length=100) 
    pl_filename_line1 = models.CharField(max_length=100) 
    pl_filename_line2 = models.CharField(max_length=100)
    
    subcontractors  = models.CharField(max_length=100)  # (gas/elec/plumb/mech/roof/septic/lowvoltage/shutters/electfromhouse)
    
    
    related_hurricane_irma = models.BooleanField() 
    project_name = models.CharField(max_length=100) 
    declared_value = models.CharField(max_length=100) 
    project_line_2 = models.CharField(max_length=100) 
    project_line_3 = models.CharField(max_length=100) 
    project_line_4 = models.CharField(max_length=100) 
    project_line_5 = models.CharField(max_length=100) 

    when_created = models.DateTimeField(
        auto_now_add=True, editable=False)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='permits',
        on_delete=models.SET_NULL)
        
    #user_id = models.IntegerField()
    order_id = models.IntegerField()

    #class Meta:
     #   verbose_name_plural = 'permits'
	
			
	
class Inspection(models.Model):
	test = models.CharField(max_length=200)
