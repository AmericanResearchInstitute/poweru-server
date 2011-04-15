from django.http import HttpResponseBadRequest
from django.shortcuts import render_to_response
import e_settings
import facade
import settings as project_settings

if e_settings.ms_provider == 'paypal':
    from paypal_svc import express_checkout as ExpressCheckout

def express_checkout_successful_return(request):
    """
    Handle GET requests coming from users who are redirected from
    Paypal after having made a payment.

    @param request HttpRequest object from django
    @type request django.http.HttpRequest
    """

    if request.method != 'GET' or 'token' not in request.GET:
        return HttpResponseBadRequest('Your request must include a string labeled "token".')

    token = request.GET['token']

    context = ExpressCheckout().complete(token)

    facade.managers.PaymentManager()._complete_express_checkout(token, context['AMT'], context['TRANSACTIONID'])

    return render_to_response('paypal/express_checkout_success.html', context)

def express_checkout_unsuccessful_return(self, request):
    """
    Handle GET requests coming from users who are redirected from
    Paypal after having not made a payment through an unsuccessful
    attempt.

    @param request    HttpRequest object from django
    @type request django.http.HttpRequest
    """

    # If we can find the token and delete it from our database, do it. If not, no sweat.
    if 'token' in request.GET:
        token = request.GET['token']
        try:
            token = paypal_ec_token.objects.get(token = token)
            token.delete()
        except paypal_ec_token.DoesNotExist:
            pass

    return render_to_response('paypal/express_checkout_no_success.html', {})
