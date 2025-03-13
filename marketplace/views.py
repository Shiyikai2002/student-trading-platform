from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Item, ItemImage, Transaction, Review, Report, UserRating, CustomUser, Offer, Cart, Wishlist, Message
from .forms import CustomUserCreationForm, ItemForm, ReportForm
import re
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from .forms import CustomUserForm



# User Registration with university email validation
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Redirect to home after successful registration
    else:
        form = CustomUserCreationForm()
    return render(request, 'marketplace/register.html', {'form': form})

# Add a new item with multiple images
@login_required
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        files = request.FILES.getlist('images')  # Retrieve multiple images
        if form.is_valid():
            item = form.save(commit=False)
            item.seller = request.user
            item.save()

            # Handle multiple images upload
            for file in files:
                ItemImage.objects.create(item=item, image=file)

            messages.success(request, "Item added successfully!")
            return redirect('home')
    else:
        form = ItemForm()
    return render(request, 'marketplace/add_item.html', {'form': form})

# Report an item for inappropriate content
@login_required
def report_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reported_by = request.user
            report.item = item
            report.save()
            messages.success(request, "Your report has been submitted.")
            return redirect('home')
    else:
        form = ReportForm()
    return render(request, 'marketplace/report_item.html', {'form': form, 'item': item})

# Confirm transaction completion by both buyer and seller
@login_required
def confirm_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    # Only the buyer or seller can confirm the transaction
    if request.user == transaction.buyer or request.user == transaction.item.seller:
        transaction.status = "Sold"
        transaction.save()
        messages.success(request, "Transaction successfully confirmed.")

    return redirect('home')

# Home page with search and filters
def home(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    # Base queryset (Available items only)
    items = Item.objects.filter(status="Available").order_by('-created_at')

    # Apply filters dynamically
    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))

    if category:
        items = items.filter(category=category)

    # Ensure featured items only include those with images
    featured_items = items.exclude(image__isnull=True).exclude(image="")[:5]

    # Extract categories dynamically
    categories = [choice[0] for choice in Item.CATEGORY_CHOICES]

    unread_messages_count = 0
    if request.user.is_authenticated:
        unread_messages_count = Message.objects.filter(receiver=request.user, is_read=False).count()

    return render(request, "marketplace/home.html", {
        "items": items.distinct(),  # Ensure unique results
        "featured_items": featured_items,
        "categories": categories,
        "unread_messages_count": unread_messages_count
    })

def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # **检查是否是管理员**
            if user.is_superuser or user.is_staff:
                return redirect('admin_dashboard')  # **跳转到管理员面板**
            else:
                return redirect('home')  # 普通用户跳转到首页
        else:
            messages.error(request, "Invalid username or password.")

    else:
        form = AuthenticationForm()
    
    return render(request, "marketplace/login.html", {"form": form})



from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import CustomUser, Item

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser and not request.user.is_staff:
        return redirect('home')  # 不是管理员则跳转到普通用户界面

    users = CustomUser.objects.all()  # 获取所有用户
    items = Item.objects.all()  # 获取所有商品
    transactions = Transaction.objects.all()  # 获取所有交易记录

    return render(request, "marketplace/admin_dashboard.html", {
        "users": users,
        "items": items,
        "transactions": transactions,  # 传递交易数据
    })


# User Logout
@login_required
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

# Buy an item
@login_required
def buy_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    # Prevent self-purchase
    if item.seller == request.user:
        messages.error(request, "You cannot buy your own item!")
        return redirect('home')

    # Ensure item availability
    if item.status != "Available":
        messages.error(request, "This item is no longer available.")
        return redirect('home')

    # Create transaction
    Transaction.objects.create(
        buyer=request.user,
        item=item,
        total_price=item.price,
        status='Pending'
    )

    # Update item status
    item.status = 'Pending'
    item.save()

    messages.success(request, "Purchase request submitted successfully!")
    return redirect('home')

# View item details
def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    reviews = Review.objects.filter(item=item)
    return render(request, 'items/item_detail.html', {'item': item, 'reviews': reviews})

# Leave a review for an item
@login_required
def leave_review(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")



        Review.objects.create(
            reviewer=request.user,
            item=item,
            rating=rating,
            comment=comment
        )
        messages.success(request, "Review submitted successfully!")
        return redirect('item_detail', item_id=item.id)

    return render(request, "items/leave_review.html", {"item": item})

# Mark an item as sold
@login_required
def mark_item_sold(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if item.seller != request.user:
        messages.error(request, "You do not have permission to mark this item as sold.")
        return redirect('home')

    item.status = "Sold"
    item.save()
    messages.success(request, "Item marked as sold successfully!")
    return redirect('home')

def search_items(request):
    """Searches for items based on user input."""
    query = request.GET.get('query', '').strip()

    if query:
        items = Item.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
        results = list(items.values('id', 'name', 'price', 'category', 'status'))
        return JsonResponse({'results': results})

    return JsonResponse({'results': []})

def search_results(request):
    query = request.GET.get('q')
    results = Item.objects.filter(name__icontains=query) if query else []
    return render(request, "marketplace/search_results.html", {"results": results, "query": query})

@login_required
def edit_item(request, item_id):
    """ Allows users or admins to edit items. """
    item = get_object_or_404(Item, id=item_id)

    # 只有管理员或该商品的卖家可以编辑
    if not (request.user == item.seller or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to edit this item.")
        return redirect('home')

    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated successfully!")
            return redirect('admin_dashboard' if request.user.is_staff or request.user.is_superuser else 'home')
    else:
        form = ItemForm(instance=item)

    return render(request, "marketplace/edit_item.html", {"form": form, "item": item})



@login_required
def delete_item(request, item_id):
    """ Allows users or admins to delete items. """
    item = get_object_or_404(Item, id=item_id)

    # 只有管理员或该商品的卖家可以删除
    if not (request.user == item.seller or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to delete this item.")
        return redirect('home')

    if request.method == "POST":
        item.delete()
        messages.success(request, "Item deleted successfully!")
        return redirect('admin_dashboard' if request.user.is_staff or request.user.is_superuser else 'home')

    return render(request, "marketplace/delete_item.html", {"item": item})


# Allow users to bid
@login_required
def make_offer(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        price = request.POST.get("price")
        Offer.objects.create(buyer=request.user, item=item, price=price)
        messages.success(request, "Offer submitted successfully!")
        return redirect('item_detail', item_id=item.id)

    return render(request, "items/make_offer.html", {"item": item})

# Bids accepted
@login_required
def accept_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, item__seller=request.user)
    offer.status = 'Accepted'
    offer.save()

    # Update product status
    offer.item.status = 'Sold'
    offer.item.save()

    messages.success(request, "Offer accepted. The item is now sold.")
    return redirect('home')

# Rejecting bids
@login_required
def reject_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, item__seller=request.user)
    offer.status = 'Rejected'
    offer.save()

    messages.success(request, "Offer rejected.")
    return redirect('home')

@login_required
def rate_user(request, user_id):
    rated_user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")
        UserRating.objects.create(rated_user=rated_user, reviewer=request.user, rating=rating, comment=comment)
        messages.success(request, "Rating submitted successfully!")
        return redirect('profile', user_id=user_id)

    return render(request, "marketplace/rate_user.html", {"rated_user": rated_user})

@login_required
def my_listings(request):
    """Show all items listed by the logged-in user."""
    items = Item.objects.filter(seller=request.user)
    return render(request, "marketplace/my_listings.html", {"items": items})

@login_required
def manage_offers(request, item_id):
    """Allows the seller to manage offers for their items."""
    item = get_object_or_404(Item, id=item_id, seller=request.user)
    offers = Offer.objects.filter(item=item)

    return render(request, "marketplace/manage_offers.html", {"item": item, "offers": offers})

def add_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, item=item)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')

def add_to_wishlist(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    Wishlist.objects.get_or_create(user=request.user, item=item)
    return redirect('wishlist')

def send_message(request, seller_id):
    seller = get_object_or_404(CustomUser, id=seller_id)
    if request.method == "POST":
        content = request.POST.get('content')
        Message.objects.create(sender=request.user, receiver=seller, content=content)
        return redirect('messages')
    return render(request, 'send_message.html', {'seller': seller})

@login_required
def profile_edit(request):
    if request.method == "POST":
        form = CustomUserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile_view')
    else:
        form = CustomUserForm(instance=request.user)

    return render(request, 'marketplace/profile_edit.html', {'form': form})


@login_required
def profile_view(request):
    return render(request, "marketplace/profile.html")

from decimal import Decimal
@login_required
def deposit(request):
    if request.method == "POST":
        amount = request.POST.get("amount")
        try:
            amount = Decimal(amount)
            if amount > 0:
                request.user.balance += amount
                request.user.save()
                messages.success(request, f"Successfully deposited ${amount:.2f}!")
            else:
                messages.error(request, "Deposit amount must be greater than zero.")
        except ValueError:
            messages.error(request, "Invalid amount entered.")
    return redirect('profile_view')


@login_required
def update_address(request):
    """ 处理用户更新地址 """
    if request.method == "POST":
        address = request.POST.get("address")
        if address:
            request.user.address = address
            request.user.save()
            messages.success(request, "Your address has been updated!")
        else:
            messages.error(request, "Address cannot be empty.")
    return redirect('profile_view')


@login_required
def confirm_purchase(request, item_id):
    """ 显示确认购买页面 """
    item = get_object_or_404(Item, id=item_id)
    if item.seller == request.user:
        messages.error(request, "You cannot buy your own item.")
        return redirect('item_detail', item_id=item.id)
    
     # 购买成功后移除购物车中的该商品
    Cart.objects.filter(user=request.user, item=item).delete()
    return render(request, 'confirm_purchase.html', {'item': item})

@login_required
def process_purchase(request, item_id):
    """ 处理购买逻辑 """
    item = get_object_or_404(Item, id=item_id)
    
    # 检查是否是卖家自己
    if item.seller == request.user:
        messages.error(request, "You cannot buy your own item.")
        return redirect('item_detail', item_id=item.id)

    if request.method == "POST":
        address = request.POST.get("address")
        
        # 检查余额是否足够
        if request.user.balance < item.price:
            messages.error(request, "Insufficient balance to complete the purchase.")
            return redirect('confirm_purchase', item_id=item.id)

        # 扣除余额
        request.user.balance -= item.price
        request.user.save()

        # 创建交易记录
        Transaction.objects.create(
            buyer=request.user,
            item=item,
            total_price=item.price,
            status="Sold"
        )

        # 更新商品状态
        item.status = "Sold"
        item.save()

        messages.success(request, f"Purchase successful! Your item will be shipped to {address}.")
        return redirect('profile_view')

    return redirect('confirm_purchase', item_id=item.id)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Transaction

@login_required
def purchase_history(request):
    """ 显示用户的购买记录 """
    transactions = Transaction.objects.filter(buyer=request.user).order_by('-date_initiated')
    return render(request, "marketplace/purchase_history.html", {"transactions": transactions})


@login_required
def add_to_cart(request, item_id):
    """ 处理添加购物车逻辑 """
    item = get_object_or_404(Item, id=item_id)

    # 防止用户添加自己出售的商品
    if item.seller == request.user:
        messages.error(request, "You cannot add your own item to the cart.")
        return redirect('item_detail', item_id=item.id)

    # 检查商品是否已经在购物车
    cart_item, created = Cart.objects.get_or_create(user=request.user, item=item)
    if created:
        messages.success(request, "Item added to your cart!")
    else:
        messages.info(request, "This item is already in your cart.")

    return redirect('cart')

@login_required
def view_cart(request):
    """ 显示购物车页面 """
    cart_items = Cart.objects.filter(user=request.user)
    return render(request, "marketplace/cart.html", {"cart_items": cart_items})


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import CustomUser, Message

@login_required
def send_message(request, receiver_id):
    """ 允许买家和卖家双方互相发送消息 """
    receiver = get_object_or_404(CustomUser, id=receiver_id)

    if request.method == "POST":
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=request.user, receiver=receiver, content=content)
            messages.success(request, "Message sent successfully!")
        else:
            messages.error(request, "Message cannot be empty.")

    return redirect("message_center_with_id", receiver_id=receiver.id)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import CustomUser, Message

@login_required
def message_center(request, receiver_id=None):
    """
    显示最近给当前用户发送信息的最新用户，并默认打开最新的聊天记录。
    """

    # **获取最近的消息（按时间降序排列，最新的在前）**
    conversations = Message.objects.filter(
        Q(receiver=request.user)  # 只获取 “别人发送给自己” 的消息
    ).order_by('-timestamp')

    unique_users = []  # 存储最近与用户聊天的对象（按最新顺序）
    seen_users = set()

    for message in conversations:
        sender = message.sender
        if sender not in seen_users:
            unique_users.append(sender)
            seen_users.add(sender)  # 避免重复添加

    # **如果 receiver_id 为空，默认选择最新给自己发消息的用户**
    if receiver_id is None and unique_users:
        return redirect('message_center_with_id', receiver_id=unique_users[0].id)  # 直接跳转到最新对话

    messages_list = []
    receiver = None

    if receiver_id:
        receiver = get_object_or_404(CustomUser, id=receiver_id)

        # **获取当前用户与 `receiver` 的所有聊天记录**
        messages_list = Message.objects.filter(
            Q(sender=request.user, receiver=receiver) |
            Q(sender=receiver, receiver=request.user)
        ).order_by("timestamp")  # 按时间升序排列（旧 → 新）

    return render(request, "marketplace/message_center.html", {
        "messages": messages_list,
        "receiver": receiver,
        "unique_users": unique_users
    })







