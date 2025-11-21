from django.contrib import admin

# Register your models here.
# http://127.0.0.1:5000/admin/transactions/transaction/ can display data in admin interface
from .models import Transaction

admin.site.register(Transaction)