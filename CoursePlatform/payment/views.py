import os
import stripe

from django.shortcuts import render, redirect, get_object_or_404, reverse
import stripe.error
from course.models import Course
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.encoding import smart_str
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv


load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
endpoint_secret = os.getenv('STRIPE_ENDPOINT_SECRET')


@login_required
def create_checkout_session(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    price_in_cents = int(course.price * 100) # Stripe must be in cents

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'unit_amount': price_in_cents,
                'product_data': {
                    'name': course.title
                },
            },
            'quantity': 1
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('course_success')),
        cancel_url=request.build_absolute_uri(reverse('course_cancel')),
        metadata={'course_id': course_id, 'user_id': request.user.id, 'user': request.user}
    )

    return redirect(session.url)


@csrf_exempt
@require_POST
def stripe_webhook(request):

    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=endpoint_secret
        )

    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        course = get_object_or_404(Course, pk=int(session['metadata']['course_id']))
        user = User.objects.get(id=int(session['metadata']['user_id']))
        course.subscribers.add(user)

    return JsonResponse({'status': 'success'})


@login_required
def course_success(request):
    return redirect('course_list')


@login_required
def course_cancel(request):
    return redirect('course_list')