from django.urls import path
from . import views

# TODO: Determine what distinct pages are required for the user stories, add a path for each in urlpatterns

app_name = "employees"
urlpatterns = [
    path('', views.index, name="index"),
    path('new/', views.create, name="create"),
    path('edit_profile/', views.edit_profile, name="edit_profile"),
    path('<int:customer_id>/pickup_confirm/', views.pickup_confirm, name="pickup_confirm"),
    path('day_filter', views.day_filter, name="day_filter"),

]