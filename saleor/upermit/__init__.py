from django.apps import AppConfig
from django.utils.translation import pgettext_lazy

import logging

logger = logging.getLogger(__name__)

class UpermitAppConfig(AppConfig):
    name = 'saleor.upermit'
    
    def ready(self):
        #logger.debug("READY READY READY READY READY READY READY READY READY READY READY READY READY READY READY READY READY READY READY READY READY ")
        from payments.signals import status_changed
        from .signals import order_status_change
        status_changed.connect(order_status_change)
        #logger.debug("STATUS_CHANGE CONNECTED STATUS_CHANGE CONNECTED STATUS_CHANGE CONNECTED STATUS_CHANGE CONNECTED STATUS_CHANGE CONNECTED STATUS_CHANGE CONNECTED STATUS_CHANGE CONNECTED ")
        
    
