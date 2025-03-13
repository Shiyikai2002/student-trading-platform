from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .views import home, edit_item, delete_item, profile_edit, message_center, profile_view, search_results
from .views import send_message, message_center  # 确保 send_message 已导入
urlpatterns = [
    # Home and Authentication
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # Item Management
    path('add_item/', views.add_item, name='add_item'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('buy/<int:item_id>/', views.buy_item, name='buy_item'),
    path('mark_sold/<int:item_id>/', views.mark_item_sold, name='mark_item_sold'),
    path('item/<int:item_id>/edit/', edit_item, name='edit_item'),
    path('item/<int:item_id>/delete/', delete_item, name='delete_item'),

    # Search & Filters
    path('search/', views.search_items, name='search_items'),

    # Reviews & Reports
    path('review/<int:item_id>/', views.leave_review, name='leave_review'),
    path('report_item/<int:item_id>/', views.report_item, name='report_item'),

    # Transaction Management
    path('confirm_transaction/<int:transaction_id>/', views.confirm_transaction, name='confirm_transaction'),

    path('make_offer/<int:item_id>/', views.make_offer, name='make_offer'),
    path('accept_offer/<int:offer_id>/', views.accept_offer, name='accept_offer'),
    path('reject_offer/<int:offer_id>/', views.reject_offer, name='reject_offer'),
    path('my_listings/', views.my_listings, name='my_listings'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('messages/', message_center, name='message_center'),

    path('profile/', profile_view, name='profile_view'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('search/', search_results, name='search_results'),

    path('deposit/', views.deposit, name='deposit'),
    path('profile/', views.profile_view, name='profile_view'),  # 确保 profile_view 也有
    path('update_address/', views.update_address, name='update_address'),  # 添加更新地址的路由

    path('item/<int:item_id>/confirm_purchase/', views.confirm_purchase, name='confirm_purchase'),
    path('item/<int:item_id>/process_purchase/', views.process_purchase, name='process_purchase'),
    path('purchase_history/', views.purchase_history, name='purchase_history'),

    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='cart'),

# Messaging System
    path("messages/", message_center, name="message_center"),
    path("messages/<int:receiver_id>/", message_center, name="message_center_with_id"),
    path("send_message/<int:receiver_id>/", send_message, name="send_message"),

    
]


