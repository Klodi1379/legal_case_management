
# clients/forms.py
from django import forms
from .models import Client, ClientContact
from secure_clients.forms import CombinedClientForm

# Use the CombinedClientForm from secure_clients app
ClientForm = CombinedClientForm
