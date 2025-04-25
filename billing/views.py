# billing/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TimeEntry, Invoice, InvoiceItem, Payment
from .forms import TimeEntryForm, InvoiceForm, InvoiceItemForm, PaymentForm
from cases.models import Case

@login_required
def time_entry_list(request):
    time_entries = TimeEntry.objects.filter(user=request.user).order_by('-date')
    return render(request, 'billing/time_entry_list.html', {'time_entries': time_entries})

@login_required
def time_entry_create(request):
    if request.method == 'POST':
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            time_entry = form.save(commit=False)
            time_entry.user = request.user
            time_entry.save()
            messages.success(request, 'Time entry created successfully.')
            return redirect('billing:time_entry_list')
    else:
        form = TimeEntryForm()
    return render(request, 'billing/time_entry_form.html', {'form': form})

@login_required
def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-issue_date')
    return render(request, 'billing/invoice_list.html', {'invoices': invoices})

@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    items = invoice.items.all()
    payments = invoice.payments.all()
    return render(request, 'billing/invoice_detail.html', {
        'invoice': invoice,
        'items': items,
        'payments': payments
    })

@login_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save()
            messages.success(request, 'Invoice created successfully.')
            return redirect('billing:invoice_detail', invoice_id=invoice.id)
    else:
        form = InvoiceForm()
    return render(request, 'billing/invoice_form.html', {'form': form})

@login_required
def invoice_item_create(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        form = InvoiceItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.invoice = invoice
            item.save()
            messages.success(request, 'Invoice item added successfully.')
            return redirect('billing:invoice_detail', invoice_id=invoice.id)
    else:
        form = InvoiceItemForm()
    return render(request, 'billing/invoice_item_form.html', {'form': form, 'invoice': invoice})

@login_required
def payment_create(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            messages.success(request, 'Payment recorded successfully.')
            return redirect('billing:invoice_detail', invoice_id=invoice.id)
    else:
        form = PaymentForm()
    return render(request, 'billing/payment_form.html', {'form': form, 'invoice': invoice})