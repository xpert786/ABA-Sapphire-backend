from django.urls import path
from .views import (
    ClientListView, ClientDetailView, SessionListCreateView, SessionDetailView, 
    RBTListView, BCBAListView, StaffListView, get_client_from_treatment_plan
)

urlpatterns = [
    # Clients
    path('clients/', ClientListView.as_view(), name='clients-list'),
    path('rbts/', RBTListView.as_view(), name='rbts-list'),
    path('bcbas/', BCBAListView.as_view(), name='bcbas-list'),
    path('staffs/', StaffListView.as_view(), name='staffs-list'),
    path('clients/<int:pk>/', ClientDetailView.as_view(), name='clients-detail'),

    # Sessions
    path('sessions/', SessionListCreateView.as_view(), name='sessions-list-create'),
    path('sessions/<int:pk>/', SessionDetailView.as_view(), name='sessions-detail'),
    
    # Treatment Plan Helper
    path('treatment-plans/<int:treatment_plan_id>/client/', get_client_from_treatment_plan, name='get-client-from-treatment-plan'),
]
