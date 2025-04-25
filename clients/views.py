# clients/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Client
from .forms import ClientForm
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.user = request.user  # Directly assign the user
            client.save()
            return redirect('clients:client_list')
    else:
        form = ClientForm()
    return render(request, 'clients/client_form.html', {'form': form})

@login_required
def client_list(request):
    clients = Client.objects.all()
    return render(request, 'clients/client_list.html', {'clients': clients})

@login_required
def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    return render(request, 'clients/client_detail.html', {'client': client})

@login_required
def client_update(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('clients:client_detail', client_id=client.id)
    else:
        form = ClientForm(instance=client)
    return render(request, 'clients/client_form.html', {'form': form})
