from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.db.models import F
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.context_processors import csrf
from django.template.response import TemplateResponse
from django.utils.translation import npgettext_lazy, pgettext_lazy
from django_prices.templatetags import prices_i18n
from payments import PaymentStatus
from prices import Money, TaxedMoney

from ...core.exceptions import InsufficientStock
from ...core.utils import ZERO_TAXED_MONEY, get_paginator_items
from ...order import OrderStatus
from ...order.emails import (
    send_fulfillment_confirmation, send_fulfillment_update)
from ...order.models import (
    Fulfillment, FulfillmentLine, Order, OrderLine, OrderNote)
from ...order.utils import update_order_status
from ...product.models import StockLocation
from ..views import staff_member_required
from .filters import OrderFilter
from .forms import (
    AddressForm, AddVariantToOrderForm, BaseFulfillmentLineFormSet,
    CancelFulfillmentForm, CancelOrderForm, CancelOrderLineForm,
    CapturePaymentForm, ChangeQuantityForm, ChangeStockForm, FulfillmentForm,
    FulfillmentLineForm, FulfillmentTrackingNumberForm, OrderNoteForm,
    RefundPaymentForm, ReleasePaymentForm, RemoveVoucherForm)
from .utils import (
    create_invoice_pdf, create_packing_slip_pdf, get_statics_absolute_url)


@staff_member_required
@permission_required('order.view_order')
def order_list(request):
    orders = Order.objects.prefetch_related(
        'payments', 'lines', 'user').order_by('-pk')
    order_filter = OrderFilter(request.GET, queryset=orders)
    orders = get_paginator_items(
        order_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'orders': orders, 'filter_set': order_filter,
        'is_empty': not order_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/order/list.html', ctx)


@staff_member_required
@permission_required('order.view_order')
def order_details(request, order_pk):
    qs = Order.objects.select_related(
        'user', 'shipping_address', 'billing_address').prefetch_related(
        'notes', 'payments', 'history', 'lines')
    order = get_object_or_404(qs, pk=order_pk)
    notes = order.notes.all()
    all_payments = order.payments.exclude(status=PaymentStatus.INPUT)
    payment = order.payments.last()
    captured = preauthorized = ZERO_TAXED_MONEY
    balance = captured - order.total
    if payment:
        can_capture = (
            payment.status == PaymentStatus.PREAUTH and
            order.status != OrderStatus.CANCELED)
        can_release = payment.status == PaymentStatus.PREAUTH
        can_refund = payment.status == PaymentStatus.CONFIRMED
        preauthorized = payment.get_total_price()
        if payment.status == PaymentStatus.CONFIRMED:
            captured = payment.get_captured_price()
            balance = captured - order.total
    else:
        can_capture = can_release = can_refund = False
    is_many_stock_locations = StockLocation.objects.count() > 1
    ctx = {'order': order, 'all_payments': all_payments, 'payment': payment,
           'notes': notes, 'captured': captured, 'balance': balance,
           'preauthorized': preauthorized, 'can_capture': can_capture,
           'can_release': can_release, 'can_refund': can_refund,
           'is_many_stock_locations': is_many_stock_locations}
    return TemplateResponse(request, 'dashboard/order/detail.html', ctx)


@staff_member_required
@permission_required('order.edit_order')
def order_add_note(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    note = OrderNote(order=order, user=request.user)
    form = OrderNoteForm(request.POST or None, instance=note)
    status = 200
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message related to an order',
            'Added note')
        order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        if note.is_public:
            form.send_confirmation_email()
    elif form.errors:
        status = 400
    ctx = {'order': order, 'form': form}
    ctx.update(csrf(request))
    template = 'dashboard/order/modal/add_note.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def capture_payment(request, order_pk, payment_pk):
    order = get_object_or_404(Order, pk=order_pk)
    payment = get_object_or_404(order.payments, pk=payment_pk)
    amount = order.total.quantize('0.01').gross
    form = CapturePaymentForm(request.POST or None, payment=payment,
                              initial={'amount': amount})
    if form.is_valid() and form.capture():
        amount = form.cleaned_data['amount']
        msg = pgettext_lazy(
            'Dashboard message related to a payment',
            'Captured %(amount)s') % {'amount': prices_i18n.amount(amount)}
        order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    status = 400 if form.errors else 200
    ctx = {'captured': payment.captured_amount, 'currency': payment.currency,
           'form': form, 'order': order, 'payment': payment}
    return TemplateResponse(request, 'dashboard/order/modal/capture.html', ctx,
                            status=status)


@staff_member_required
@permission_required('order.edit_order')
def refund_payment(request, order_pk, payment_pk):
    order = get_object_or_404(Order, pk=order_pk)
    payment = get_object_or_404(order.payments, pk=payment_pk)
    amount = payment.captured_amount
    form = RefundPaymentForm(request.POST or None, payment=payment,
                             initial={'amount': amount})
    if form.is_valid() and form.refund():
        amount = form.cleaned_data['amount']
        msg = pgettext_lazy(
            'Dashboard message related to a payment',
            'Refunded %(amount)s') % {'amount': prices_i18n.amount(amount)}
        order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    status = 400 if form.errors else 200
    ctx = {'captured': payment.captured_amount, 'currency': payment.currency,
           'form': form, 'order': order, 'payment': payment}
    return TemplateResponse(request, 'dashboard/order/modal/refund.html', ctx,
                            status=status)


@staff_member_required
@permission_required('order.edit_order')
def release_payment(request, order_pk, payment_pk):
    order = get_object_or_404(Order, pk=order_pk)
    payment = get_object_or_404(order.payments, pk=payment_pk)
    form = ReleasePaymentForm(request.POST or None, payment=payment)
    if form.is_valid() and form.release():
        msg = pgettext_lazy('Dashboard message', 'Released payment')
        order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    status = 400 if form.errors else 200
    ctx = {'captured': payment.captured_amount, 'currency': payment.currency,
           'form': form, 'order': order, 'payment': payment}
    return TemplateResponse(request, 'dashboard/order/modal/release.html', ctx,
                            status=status)


@staff_member_required
@permission_required('order.edit_order')
def orderline_change_quantity(request, order_pk, line_pk):
    order = get_object_or_404(Order, pk=order_pk)
    line = get_object_or_404(order.lines.all(), pk=line_pk)
    form = ChangeQuantityForm(request.POST or None, instance=line)
    status = 200
    old_quantity = line.quantity
    if form.is_valid():
        msg = pgettext_lazy(
            'Dashboard message related to an order line',
            'Changed quantity for product %(product)s from'
            ' %(old_quantity)s to %(new_quantity)s') % {
                'product': line.product, 'old_quantity': old_quantity,
                'new_quantity': line.quantity}
        with transaction.atomic():
            order.history.create(content=msg, user=request.user)
            form.save()
            messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'object': line, 'form': form}
    template = 'dashboard/order/modal/change_quantity.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def orderline_cancel(request, order_pk, line_pk):
    order = get_object_or_404(Order, pk=order_pk)
    line = get_object_or_404(order.lines.all(), pk=line_pk)
    form = CancelOrderLineForm(data=request.POST or None, line=line)
    status = 200
    if form.is_valid():
        msg = pgettext_lazy(
            'Dashboard message related to an order line',
            'Cancelled item %s') % line
        with transaction.atomic():
            order.history.create(content=msg, user=request.user)
            form.cancel_line()
            messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'item': line, 'form': form}
    return TemplateResponse(
        request, 'dashboard/order/modal/cancel_line.html',
        ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def add_variant_to_order(request, order_pk):
    """Add variant in given quantity to an order."""
    order = get_object_or_404(Order, pk=order_pk)
    form = AddVariantToOrderForm(
        request.POST or None, order=order, discounts=request.discounts)
    status = 200
    if form.is_valid():
        msg_dict = {
            'quantity': form.cleaned_data.get('quantity'),
            'variant': form.cleaned_data.get('variant')}
        try:
            with transaction.atomic():
                form.save()
            msg = pgettext_lazy(
                'Dashboard message related to an order',
                'Added %(quantity)d x %(variant)s') % msg_dict
            order.history.create(content=msg, user=request.user)
            messages.success(request, msg)
        except InsufficientStock:
            msg = pgettext_lazy(
                'Dashboard message related to an order',
                'Insufficient stock: could not add %(quantity)d x %(variant)s'
            ) % msg_dict
            messages.warning(request, msg)
        return redirect('dashboard:order-details', order_pk=order_pk)
    elif form.errors:
        status = 400
    ctx = {'order': order, 'form': form}
    template = 'dashboard/order/modal/add_variant_to_order.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def address_view(request, order_pk, address_type):
    order = Order.objects.get(pk=order_pk)
    if address_type == 'shipping':
        address = order.shipping_address
        success_msg = pgettext_lazy(
            'Dashboard message',
            'Updated shipping address')
    else:
        address = order.billing_address
        success_msg = pgettext_lazy(
            'Dashboard message',
            'Updated billing address')
    form = AddressForm(request.POST or None, instance=address)
    if form.is_valid():
        updated_address = form.save()
        if address is None:
            if address_type == 'shipping':
                order.shipping_address = updated_address
            else:
                order.billing_address = updated_address
            order.save()
        order.history.create(content=success_msg, user=request.user)
        messages.success(request, success_msg)
        return redirect('dashboard:order-details', order_pk=order_pk)
    ctx = {'order': order, 'address_type': address_type, 'form': form}
    return TemplateResponse(request, 'dashboard/order/address_form.html', ctx)


@staff_member_required
@permission_required('order.edit_order')
def cancel_order(request, order_pk):
    status = 200
    order = get_object_or_404(Order, pk=order_pk)
    form = CancelOrderForm(request.POST or None, order=order)
    if form.is_valid():
        msg = pgettext_lazy('Dashboard message', 'Order canceled')
        with transaction.atomic():
            form.cancel_order()
            if form.cleaned_data.get('restock'):
                restock_msg = npgettext_lazy(
                    'Dashboard message',
                    'Restocked %(quantity)d item',
                    'Restocked %(quantity)d items',
                    'quantity') % {'quantity': order.get_total_quantity()}
                order.history.create(content=restock_msg, user=request.user)
            order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
        # TODO: send status confirmation email
    elif form.errors:
        status = 400
    ctx = {'form': form, 'order': order}
    return TemplateResponse(
        request, 'dashboard/order/modal/cancel_order.html', ctx,
        status=status)


@staff_member_required
@permission_required('order.edit_order')
def remove_order_voucher(request, order_pk):
    status = 200
    order = get_object_or_404(Order, pk=order_pk)
    form = RemoveVoucherForm(request.POST or None, order=order)
    if form.is_valid():
        msg = pgettext_lazy('Dashboard message', 'Removed voucher from order')
        with transaction.atomic():
            form.remove_voucher()
            order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {'order': order}
    return TemplateResponse(request,
                            'dashboard/order/modal/order_remove_voucher.html',
                            ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def order_invoice(request, order_pk):
    orders = Order.objects.prefetch_related(
        'user', 'shipping_address', 'billing_address', 'voucher')
    order = get_object_or_404(orders, pk=order_pk)
    absolute_url = get_statics_absolute_url(request)
    pdf_file, order = create_invoice_pdf(order, absolute_url)
    response = HttpResponse(pdf_file, content_type='application/pdf')
    name = "invoice-%s" % order.id
    response['Content-Disposition'] = 'filename=%s' % name
    return response


@staff_member_required
@permission_required('order.edit_order')
def fulfillment_packing_slips(request, order_pk, fulfillment_pk):
    orders = Order.objects.prefetch_related(
        'user', 'shipping_address', 'billing_address')
    order = get_object_or_404(orders, pk=order_pk)
    fulfillments = order.fulfillments.prefetch_related(
        'lines', 'lines__order_line')
    fulfillment = get_object_or_404(fulfillments, pk=fulfillment_pk)
    absolute_url = get_statics_absolute_url(request)
    pdf_file, order = create_packing_slip_pdf(order, fulfillment, absolute_url)
    response = HttpResponse(pdf_file, content_type='application/pdf')
    name = "packing-slip-%s" % (order.id,)
    response['Content-Disposition'] = 'filename=%s' % name
    return response


@staff_member_required
@permission_required('order.edit_order')
def orderline_change_stock(request, order_pk, line_pk):
    line = get_object_or_404(OrderLine, pk=line_pk)
    status = 200
    form = ChangeStockForm(request.POST or None, instance=line)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message',
            'Stock location changed for %s') % form.instance.product_sku
        messages.success(request, msg)
    elif form.errors:
        status = 400
    ctx = {'order_pk': order_pk, 'line_pk': line_pk, 'form': form}
    template = 'dashboard/order/modal/order_line_stock.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def fulfill_order_lines(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    unfulfilled_lines = order.lines.filter(
        quantity_fulfilled__lt=F('quantity'))
    status = 200
    form = FulfillmentForm(
        request.POST or None, order=order, instance=Fulfillment())
    FulfillmentLineFormSet = modelformset_factory(
        FulfillmentLine, form=FulfillmentLineForm, extra=len(unfulfilled_lines),
        formset=BaseFulfillmentLineFormSet)
    initial = [
        {'order_line': line, 'quantity': line.quantity_unfulfilled}
        for line in unfulfilled_lines]
    formset = FulfillmentLineFormSet(
        request.POST or None, queryset=FulfillmentLine.objects.none(),
        initial=initial)
    all_forms_valid = all([line_form.is_valid() for line_form in formset])
    if all_forms_valid and form.is_valid():
        forms_to_save = [
            line_form for line_form in formset
            if line_form.cleaned_data.get('quantity') > 0]
        if forms_to_save:
            fulfillment = form.save()
            quantity_fulfilled = 0
            for line_form in forms_to_save:
                line = line_form.save(commit=False)
                line.fulfillment = fulfillment
                line.save()
                quantity_fulfilled += line_form.cleaned_data.get('quantity')
            update_order_status(order)
            msg = npgettext_lazy(
                'Dashboard message related to an order',
                'Fulfilled %(quantity_fulfilled)d item',
                'Fulfilled %(quantity_fulfilled)d items',
                'quantity_fulfilled') % {
                    'quantity_fulfilled': quantity_fulfilled}
            order.history.create(content=msg, user=request.user)
            if form.cleaned_data.get('send_mail'):
                send_fulfillment_confirmation.delay(order.pk, fulfillment.pk)
                send_mail_msg = pgettext_lazy(
                    'Dashboard message related to an order',
                    'Shipping confirmation email was sent to user'
                    '(%(email)s)') % {'email': order.get_user_current_email()}
                order.history.create(content=send_mail_msg, user=request.user)
        else:
            msg = pgettext_lazy(
                'Dashboard message related to an order', 'No items fulfilled')
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {
        'form': form, 'formset': formset, 'order': order,
        'unfulfilled_lines': unfulfilled_lines}
    template = 'dashboard/order/fulfillment.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('order.edit_order')
def cancel_fulfillment(request, order_pk, fulfillment_pk):
    status = 200
    order = get_object_or_404(Order, pk=order_pk)
    fulfillment = get_object_or_404(
        order.fulfillments.all(), pk=fulfillment_pk)
    form = CancelFulfillmentForm(request.POST or None, fulfillment=fulfillment)
    if form.is_valid():
        msg = pgettext_lazy(
            'Dashboard message', 'Fulfillment #%(fulfillment)s canceled') % {
                'fulfillment': fulfillment.composed_id}
        with transaction.atomic():
            form.cancel_fulfillment()
            if form.cleaned_data.get('restock'):
                restock_msg = npgettext_lazy(
                    'Dashboard message',
                    'Restocked %(quantity)d item',
                    'Restocked %(quantity)d items',
                    'quantity') % {
                        'quantity': fulfillment.get_total_quantity()}
                order.history.create(content=restock_msg, user=request.user)
            order.history.create(content=msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {'form': form, 'order': order, 'fulfillment': fulfillment}
    return TemplateResponse(
        request, 'dashboard/order/modal/cancel_fulfillment.html', ctx,
        status=status)


@staff_member_required
@permission_required('order.edit_order')
def change_fulfillment_tracking(request, order_pk, fulfillment_pk):
    status = 200
    order = get_object_or_404(Order, pk=order_pk)
    fulfillment = get_object_or_404(
        order.fulfillments.all(), pk=fulfillment_pk)
    form = FulfillmentTrackingNumberForm(
        request.POST or None, instance=fulfillment)
    if form.is_valid():
        form.save()
        if fulfillment.tracking_number:
            msg = pgettext_lazy(
                'Dashboard message',
                'Fulfillment #%(fulfillment)s tracking number changed to: '
                '#%(tracking_number)s') % {
                    'fulfillment': fulfillment.composed_id,
                    'tracking_number': fulfillment.tracking_number}
        else:
            msg = pgettext_lazy(
                'Dashboard message',
                'Fulfillment #%(fulfillment)s tracking number removed') % {
                    'fulfillment': fulfillment.composed_id}
        order.history.create(content=msg, user=request.user)
        if form.cleaned_data.get('send_mail'):
            send_fulfillment_update.delay(order.pk, fulfillment.pk)
            send_mail_msg = pgettext_lazy(
                'Dashboard message related to an order',
                'Shipping update email was sent to user (%(email)s)') % {
                    'email': order.get_user_current_email()}
            order.history.create(content=send_mail_msg, user=request.user)
        messages.success(request, msg)
        return redirect('dashboard:order-details', order_pk=order.pk)
    elif form.errors:
        status = 400
    ctx = {'form': form, 'order': order, 'fulfillment': fulfillment}
    return TemplateResponse(
        request, 'dashboard/order/modal/fulfillment_tracking.html', ctx,
        status=status)


@staff_member_required
@permission_required('order.edit_order')
def order_permit_pdf(request, order_pk):
    orders = Order.objects.prefetch_related(
        'user', 'shipping_address', 'billing_address', 'voucher')
    order = get_object_or_404(orders, pk=order_pk)
    absolute_url = get_statics_absolute_url(request)

#    rendered_template = get_template(INVOICE_TEMPLATE).render(ctx)

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
#    can.drawString(10, 700, order)

#    i=700
#
#    for attr in dir(order.created):
#        if hasattr( order.created, attr ):
#            can.drawString(10, i, "order.%s = %s" % (attr, getattr(order.created, attr)))
#            i=i-5
# Start a new page.
#    can.showPage()


#--------------------
# Handle time/date formats here.
# order.created = 2018-04-22 20:17:35.283285+00:00

#--------------------
# Start populating the checkboxes (page 1)

    can.setFont("Times-Roman", 18)

    # Contractor
    can.drawString(155, 604, "X")

    # 1 & 2 Family Dwelling / Townhouse
    can.drawString(141, 623, "X")

    # Mobile/Manufactured home
    can.drawString(270, 623, "X")

    # Design Professional
    can.drawString(303, 604, "X")

    # Residential 3+ units/Multi-family
    can.drawString(388, 623, "X")

    # Commercial
    can.drawString(523, 623, "X")

    # Owner Builder
    can.drawString(485, 604, "X")


#-------------------------------
# Start populating the Property Information (page 1)

    # Reset the font in case it was changed elsewhere
    can.setFont("Times-Roman", 11)

    # Those are 13 y units apart
    can.drawString(120, 574, "Parcel/Folio Line 1234567890")

    can.drawString(120, 561, order.billing_address.street_address_1)
#    can.drawString(120, 561, "Address Line 1 12345678901234567890")
#    can.drawString(120, 548, "Address Line 2 12345678901234567890")

    addr2=order.billing_address.street_address_2 + " " + order.billing_address.city + ", " + order.billing_address.country_area + " " + order.billing_address.postal_code


    can.drawString(120, 548, addr2)


    # 14 units..
    can.drawString(120, 534, order.billing_address.full_name) # Owner name

    # 13 units
    can.drawString(120, 521, order.billing_address.phone.as_national) # Owner phone

    can.drawString(120, 508, "Subdivision")
    
    # etc. 
    can.drawString(120, 494, "Lot/Block/Unit")
    can.drawString(120, 481, "SDP/PL#")
    can.drawString(120, 468, "PL# Filename Line 1")
    can.drawString(120, 455, "PL# Filename Line 2")


#-----------------------
# Start populating application information
    can.setFont("Times-Roman", 16)

    # Sub contractors.
    # Elec
    can.drawString(120, 410, "X")

    # Plumb
    can.drawString(157, 410, "X")

    # Mech
    can.drawString(208, 410, "X")

    # Roof
    can.drawString(256, 410, "X")

    # Septic
    can.drawString(299, 410, "X")

    # Low Voltage
    can.drawString(342, 410, "X")

    # Shutters
    can.drawString(407, 410, "X")

    # ELECT from house
    can.drawString(455, 410, "X")

    # Gas
    can.drawString(540, 410, "X")


    # Related to Hurricane Irma
    # No
    can.drawString(553, 335, "X")
    # Yes
    can.drawString(518, 335, "X")


#----------------------
# Start populating project information

    # Reset the font in case it was changed elsewhere
    can.setFont("Times-Roman", 11)

    # Project name
    can.drawString(278, 303, "Project Name")

    # Declared Value
    can.drawString(504, 303, "Declared Value")

    # Line 2
    can.drawString(23, 274, "Line 2 1234567890123456789012345678901234567890")

    # Line 3
    can.drawString(23, 260, "Line 3 1234567890123456789012345678901234567890")

    # Line 4
    can.drawString(23, 246, "Line 4 1234567890123456789012345678901234567890")

    # Line 5
    can.drawString(23, 232, "Line 5 1234567890123456789012345678901234567890")


#-----------------------
# Start a new page.
    can.showPage()

    # Section A
#    can.drawString(282,452,"23rd")     # Day
#    can.drawString(353,452,"December")  # Month
#    can.drawString(462,452,"18")   # Year

    can.drawString(282,452,order.created.strftime("%d"))     # Day
    can.drawString(353,452,order.created.strftime("%B"))  # Month
    can.drawString(462,452,order.created.strftime("%y"))   # Year



    # Section B
#    can.drawString(282,325,"23rd")     # Day
#    can.drawString(353,325,"December")  # Month
#    can.drawString(462,325,"18")   # Year

    can.drawString(282,325,order.created.strftime("%d"))     # Day
    can.drawString(353,325,order.created.strftime("%B"))  # Month
    can.drawString(462,325,order.created.strftime("%y"))   # Year


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
    name = "permit-%s" % order.id
    response['Content-Disposition'] = 'filename=%s' % name
    return response

