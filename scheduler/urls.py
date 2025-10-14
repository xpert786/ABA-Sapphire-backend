from django.urls import path
from .views import ClientListView, ClientDetailView, SessionListCreateView, SessionDetailView, RBTListView, BCBAListView

urlpatterns = [
    # Clients
    path('clients/', ClientListView.as_view(), name='clients-list'),
    path('rbts/', RBTListView.as_view(), name='clients-list'),
    path('bcbas/', BCBAListView.as_view(), name='clients-list'),
    path('clients/<int:pk>/', ClientDetailView.as_view(), name='clients-detail'),

    # Sessions
    path('sessions/', SessionListCreateView.as_view(), name='sessions-list-create'),
    path('sessions/<int:pk>/', SessionDetailView.as_view(), name='sessions-detail'),
]
