from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("search/", views.ProductSearchView.as_view(), name="search"),
    path("search/suggestions/", views.ProductSuggestionsView.as_view(), name="search-suggestions"),
    path("cart/", views.CartListCreateView.as_view(), name="cart-list-create"),
    path("cart/<uuid:cart_item_id>/", views.CartItemDetailView.as_view(), name="cart-item-detail"),
]
