import logging

from django.utils.translation import pgettext_lazy

from django.db import models

from ..core import analytics
#from .emails import send_order_confirmation

from .models import Permit

from ..order.models import OrderLine

logger = logging.getLogger(__name__)


def order_status_change(sender, instance, **kwargs):
    """Handle payment status change and set suitable order status."""
    order = instance.order
    if order.is_fully_paid():
        '''
        order.history.create(
            content=pgettext_lazy(
                'Order status history entry', 'Order fully paid'))
        send_order_confirmation.delay(order.pk)
        '''
        #logger.debug("creating permit object..")
        
        # Figure out how many orders..
#        ol = OrderLine()
        
        
        p = Permit(order_id=order.id, user_id=order.user_id)
        p.order_id = order.id
        p.user_id = order.user_id
        p.save()
        
        
        #logger.exception('SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT SAVED PERMIT OBJECT ')
        '''
        try:
            analytics.report_order(order.tracking_client_id, order)
        except Exception:
            # Analytics failing should not abort the checkout flow
            logger.exception('Recording order in analytics failed')
        '''
