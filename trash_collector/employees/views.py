from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from datetime import date
import calendar
from django.apps import apps
from .models import Employee
import urllib.parse #will parse address into url-encoded string
import json
import requests


#from trash_collector.customers.models import Customer

# Create your views here.
# TODO: Create a function for each path created in employees/urls.py. Each will need a template as well.

def get_lat_long(name, formatted_address):
    GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/geocode/json?' + 'address=' + formatted_address + '&key=AIzaSyAdcmYw8bA-nE2XT0l45JmlWMDQHfKkzdY'
    
    params ={
        'address': formatted_address,
        'sensor': 'false',
        'region': 'United States'
    }
    
    req = requests.get(GOOGLE_MAPS_API_URL, params=params)
    res = req.json()
    
    result = res['results'][0]
    lat = result['geometry']['location']['lat']
    long = result['geometry']['location']['lng']
    
    return [name, lat, long]

@login_required
def index(request):
    # The following line will get the logged-in user (if there is one) within any view function
    logged_in_user = request.user
    try:
        # This line will return the employee record of the logged-in user if one exists
        logged_in_employee = Employee.objects.get(user=logged_in_user)
        today = date.today()
        today_weekday_number = today.weekday()
        today_weekday = calendar.day_name[today_weekday_number]

        Customer = apps.get_model('customers.Customer')
        
        customer_weekday_pickup = Customer.objects.filter(zip_code=logged_in_employee.zip_code).filter(weekly_pickup=today_weekday).exclude(date_of_last_pickup=today).exclude(suspend_start__lte=today, suspend_end__gte=today)
        customer_onetime_pickup = Customer.objects.filter(zip_code=logged_in_employee.zip_code).filter(one_time_pickup=today).exclude(date_of_last_pickup=today).exclude(suspend_start__lte=today, suspend_end__gte=today)
        
        customer_addresses = []
        
        for customer in customer_weekday_pickup:
            address = customer.address + ' '+ customer.zip_code
            customer_url = urllib.parse.quote(address)
            customer_geocode = get_lat_long(customer.name, customer_url)
            customer_addresses.append(customer_geocode)
        
        for customer in customer_onetime_pickup:
            address = customer.address + ' '+ customer.zip_code
            customer_url = urllib.parse.quote(address)
            customer_geocode = get_lat_long(customer.name, customer_url)
            customer_addresses.append(customer_geocode)
        
        data_visualization = [item for item in customer_weekday_pickup]
        
        context ={
            'logged_in_employee': logged_in_employee,
            'today': today,
            'customer_weekday_pickup': customer_weekday_pickup,
            'customer_onetime_pickup': customer_onetime_pickup,
            'customer_addresses': json.dumps(customer_addresses),
        }
        return render(request, 'employees/index.html', context)

        
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('employees:create'))

@login_required
def create(request):
    logged_in_user = request.user
    if request.method == "POST":
        name_from_form = request.POST.get('name')
        zip_from_form = request.POST.get('zip_code')        
        new_employee = Employee(name=name_from_form, user=logged_in_user, zip_code=zip_from_form)
        new_employee.save()
        return HttpResponseRedirect(reverse('employees:index'))
    else:
        return render(request, 'employees/create.html')

@login_required
def edit_profile(request):
    logged_in_user = request.user
    logged_in_employee = Employee.objects.get(user=logged_in_user)
    if request.method == "POST":
        name_from_form = request.POST.get('name')        
        zip_from_form = request.POST.get('zip_code')
        logged_in_employee.name = name_from_form        
        logged_in_employee.zip_code = zip_from_form        
        logged_in_employee.save()
        return HttpResponseRedirect(reverse('employees:index'))
    else:
        context = {
            'logged_in_employee': logged_in_employee
        }
        return render(request, 'employees/edit_profile.html', context)

@login_required
def pickup_confirm(request, customer_id):
    logged_in_user = request.user
    logged_in_employee = Employee.objects.get(user=logged_in_user)
    
    if request.method == 'POST':
        confirm = request.POST.get('confirm')
        if confirm == 'Yes':
            Customer = apps.get_model('customers.Customer')
            customer_pickup = Customer.objects.get(pk=customer_id)
            customer_pickup.balance += 20
            customer_pickup.date_of_last_pickup = date.today()
            customer_pickup.save()
            return HttpResponse('<script type="text/javascript">window.close(); window.opener.location.reload();</script>')
        else:
            return HttpResponse('<script type="text/javascript">window.close();</script>')
    
    else:
        Customer = apps.get_model('customers.Customer')
        customer_pickup = Customer.objects.get(pk=customer_id)
        context = {'customer_pickup': customer_pickup,
                   'logged_in_employee': logged_in_employee}
        return render (request, 'employees/pickup_confirm.html', context)

@login_required
def day_filter(request):
    
    logged_in_user = request.user
    logged_in_employee = Employee.objects.get(user=logged_in_user)

    if request.method == 'POST':
        day_from_form = request.POST.get('day')
        if day_from_form is None:
            day_statement = 'Please Select A Day From Above'
        else:
            day_statement = str(day_from_form) + "'s" +' ' + 'Scheduled' + ' ' +'Pickups'
        
        Customer = apps.get_model('customers.Customer')
        customer_day_pickup = Customer.objects.filter(zip_code=logged_in_employee.zip_code).filter(weekly_pickup=day_from_form)
        
        data_visualization = [item for item in customer_day_pickup]
        
        context ={
            'day': day_statement,
            'logged_in_employee': logged_in_employee,
            'customer_day_pickup': customer_day_pickup
        }
        return render(request, 'employees/day_filter.html', context)

    else:
        return render(request, 'employees/day_filter.html')

@login_required
def customer_address(request, customer_id):
    logged_in_user = request.user
    logged_in_employee = Employee.objects.get(user=logged_in_user)

    Customer = apps.get_model('customers.Customer')
    customer = Customer.objects.get(pk=customer_id)
    customer_address = customer.address
    customer_zip = customer.zip_code
    customer_full_address = customer_address + ' '+ customer_zip
    customer_url = urllib.parse.quote(customer_full_address)
    
    context = {'customer': customer,
                'logged_in_employee': logged_in_employee,
                'customer_full_address': customer_full_address,
                'customer_url': customer_url}
    
    return render (request, 'employees/customer_address.html', context)