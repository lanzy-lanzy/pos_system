# Imports
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Sum, Count, F, Avg
from django.db.models.functions import TruncDate, TruncMonth
from io import BytesIO
from .models import Product, Transaction, TransactionItem
import qrcode
import base64
import json
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from django.contrib.admin.views.decorators import staff_member_required

logger = logging.getLogger(__name__)

def admin_required(view_func):
    decorated_view_func = login_required(staff_member_required(view_func))
    return decorated_view_func

# Cart Views
def view_cart(request):
    cart = request.session.get('cart', [])
    products = Product.objects.filter(id__in=[item['id'] for item in cart])
    total = sum(product.price * item['quantity'] for product, item in zip(products, cart))
    return render(request, 'pos/view_cart.html', {'products': products, 'total': total})

def remove_from_cart(request, product_id):
    cart = [item for item in request.session.get('cart', []) if item['id'] != product_id]
    request.session['cart'] = cart
    return redirect('view_cart')

# Checkout and Payment Processing Views
@csrf_exempt
def checkout(request):
    if request.method == 'POST':
        cart = request.session.get('cart', [])
        
        if not cart:
            return JsonResponse({'success': False, 'error': 'Cart is empty'})
        
        total = sum(float(item['price']) * item['quantity'] for item in cart)
        
        # Create Transaction
        transaction = Transaction.objects.create(total_amount=total, date_time=timezone.now())        
        for item in cart:
            product = get_object_or_404(Product, id=item['id'])
            TransactionItem.objects.create(transaction=transaction, product=product, quantity=item['quantity'], price=item['price'])

        # Generate QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(str(transaction.transaction_id))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_image = base64.b64encode(buffer.getvalue()).decode()

        request.session['cart'] = []

        return JsonResponse({
            'success': True,
            'qr_image': f"data:image/png;base64,{qr_image}",
            'transaction_id': str(transaction.transaction_id)
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Transaction
import json

@csrf_exempt
def process_payment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        transaction_id = data.get('transaction_id')
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            transaction.mark_as_complete()
            return JsonResponse({'success': True, 'message': 'Payment processed successfully!'})
        except Transaction.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Transaction not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return render(request, 'pos/process_payment.html')

# Product Scanning and Cart Management
@csrf_exempt
def scan_product(request):
    if request.method == 'POST':
        barcode = request.POST.get('barcode')
        try:
            product = Product.objects.get(barcode=barcode)
            cart = request.session.get('cart', [])
            existing_item = next((item for item in cart if item['id'] == product.id), None)
            
            if existing_item:
                existing_item['quantity'] += 1
            else:
                cart.append({
                    'id': product.id,
                    'quantity': 1,
                    'price': str(product.price)
                })

            request.session['cart'] = cart
            return JsonResponse({'success': True})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})

    # Display Cart
    cart = request.session.get('cart', [])
    cart_items = []
    total = 0
    for item in cart:
        product = get_object_or_404(Product, id=item['id'])
        subtotal = product.price * item['quantity']
        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
            'subtotal': subtotal
        })
        total += subtotal

    return render(request, 'pos/scan_product.html', {'cart_items': cart_items, 'total': total})

@csrf_exempt
def update_cart_item(request):
    if request.method == 'POST':
        product_id = int(request.POST.get('product_id'))
        quantity = int(request.POST.get('quantity'))
        cart = request.session.get('cart', [])

        for item in cart:
            if item['id'] == product_id:
                item['quantity'] = quantity
                break

        request.session['cart'] = cart
        total = sum(float(item['price']) * item['quantity'] for item in cart)

        return JsonResponse({'success': True, 'total': total})

    return JsonResponse({'success': False})

@csrf_exempt
def delete_cart_item(request):
    if request.method == 'POST':
        product_id = int(request.POST.get('product_id'))
        cart = [item for item in request.session.get('cart', []) if item['id'] != product_id]
        request.session['cart'] = cart
        total = sum(float(item['price']) * item['quantity'] for item in cart)
        
        return JsonResponse({'success': True, 'total': total})

    return JsonResponse({'success': False})

# Transaction History
@login_required
def transaction_history(request):
    transactions_list = Transaction.objects.all().order_by('-date_time')
    paginator = Paginator(transactions_list, 10)  # 10 transactions per page
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)
    return render(request, 'pos/transaction_history.html', {'transactions': transactions})

@require_http_methods(["POST"])
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
    transaction.delete()
    return JsonResponse({'success': True})

from django.http import JsonResponse
from .models import Transaction
from django.shortcuts import get_object_or_404
from uuid import UUID

def get_transaction_details(request):
    transaction_id = request.GET.get('transaction_id')
    
    if not transaction_id:
        return JsonResponse({'error': 'No transaction ID provided'}, status=400)
    
    try:
        UUID(transaction_id)
    except ValueError:
        return JsonResponse({'error': 'Invalid transaction ID'}, status=400)
    
    transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
    
    items = [
        {
            'name': item.product.name,
            'price': str(item.price),
            'quantity': item.quantity
        }
        for item in transaction.items.all()
    ]
    return JsonResponse({
        'transaction_id': str(transaction.transaction_id),
        'items': items,
        'total': str(transaction.total_amount),
        'date_time': transaction.date_time.isoformat()
    })

# Sales Reports
@admin_required
def sales_report(request):
    daily_sales = Transaction.objects.annotate(date=TruncDate('date_time')).values('date').annotate(
        total_sales=Sum('total_amount'), transactions_count=Count('id')).order_by('-date')

    top_products = TransactionItem.objects.values('product__name').annotate(
        total_quantity=Sum('quantity'), total_sales=Sum(F('price') * F('quantity'))).order_by('-total_quantity')[:10]

    monthly_sales = Transaction.objects.annotate(month=TruncMonth('date_time')).values('month').annotate(
        total_sales=Sum('total_amount'), transactions_count=Count('id')).order_by('-month')

    context = {
        'daily_sales': daily_sales,
        'top_products': top_products,
        'monthly_sales': monthly_sales,
    }
    return render(request, 'pos/sales_report.html', context)

@admin_required
def generate_sales_report_pdf(request):
    monthly_sales = Transaction.objects.annotate(month=TruncMonth('date_time')).values('month').annotate(
        total_sales=Sum('total_amount'), transactions_count=Count('id'), avg_transaction=Avg('total_amount')).order_by('-month')

    top_products = TransactionItem.objects.values('product__name').annotate(
        total_quantity=Sum('quantity'), total_sales=Sum(F('price') * F('quantity'))).order_by('-total_quantity')[:10]

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Title and Chart
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Sales Report", styles['Heading1']))
    elements.append(Spacer(1, 0.25 * inch))

    plt.figure(figsize=(8, 4))
    sns.lineplot(x=[sale['month'].strftime("%Y-%m") for sale in monthly_sales], y=[sale['total_sales'] for sale in monthly_sales])
    plt.title("Monthly Sales")
    plt.xlabel("Month")
    plt.ylabel("Sales")

    plt.savefig(buffer, format="PNG")
    buffer.seek(0)
    elements.append(Image(buffer, 6 * inch, 3 * inch))

    buffer.seek(0)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
    response.write(pdf)
    return response

from django.core.exceptions import PermissionDenied

def check_admin_session(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper

# @check_admin_session
# def admin_only_view(request):
#     # ... admin-only view logic ...
