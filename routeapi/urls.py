# routeapi/urls.py
from django.urls import path
from .views import RouteFuelAPIView
from .views_ui import RouteUI
from .views import RouteResultDetailAPIView  # if you added persistence

urlpatterns = [
    path('route/', RouteFuelAPIView.as_view(), name='route-fuel'),
    path('ui/', RouteUI.as_view(), name='route-ui'),           # ← UI page at /api/ui/
    path('results/<uuid:pk>/', RouteResultDetailAPIView.as_view(), name='route-result-detail'),  # optional
]

