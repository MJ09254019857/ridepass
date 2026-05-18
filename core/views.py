from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal, InvalidOperation
from .models import Wallet, Route, Ticket, Transaction, Notification, UserProfile

# -- Helpers ------------------------------------------------------------------
def get_wallet(user): w,_=Wallet.objects.get_or_create(user=user); return w
def get_profile(user): p,_=UserProfile.objects.get_or_create(user=user); return p
def add_notif(user,title,msg,icon='🔔'): Notification.objects.create(user=user,title=title,message=msg,icon=icon)
def unread(user): return Notification.objects.filter(user=user,is_read=False).count()
def is_admin(user): return user.is_authenticated and user.is_staff

# -- Auth ---------------------------------------------------------------------
def landing(request):
    return render(request,'core/landing.html')

def login_view(request):
    if request.user.is_authenticated: return redirect('dashboard')
    if request.method=='POST':
        email=request.POST.get('email','')
        password=request.POST.get('password','')
        username=email
        try:
            uo=User.objects.get(email=email); username=uo.username
        except User.DoesNotExist: pass
        user=authenticate(request,username=username,password=password)
        if user:
            login(request,user)
            return redirect('admin_dashboard' if user.is_staff else 'dashboard')
        messages.error(request,'Invalid email or password.')
    return render(request,'core/login.html')

def logout_view(request):
    logout(request); return redirect('landing')

def register_view(request):
    if request.user.is_authenticated: return redirect('dashboard')
    if request.method=='POST':
        email=request.POST.get('email','')
        password=request.POST.get('password','')
        full_name=request.POST.get('full_name','')
        username=email.split('@')[0]
        base=username; i=1
        while User.objects.filter(username=username).exists():
            username=f"{base}{i}"; i+=1
        if User.objects.filter(email=email).exists():
            messages.error(request,'Email already exists.')
        else:
            names=full_name.strip().split(' ',1)
            user=User.objects.create_user(username=username,email=email,password=password,
                first_name=names[0] if names else '',last_name=names[1] if len(names)>1 else '')
            get_wallet(user); get_profile(user)
            add_notif(user,'Welcome to RidePass!','Your account is ready. Top up to buy tickets.','🎉')
            messages.success(request,'Account created successfully! Please log in.')
            return redirect('login')
    return render(request,'core/register.html')

# -- User Dashboard -----------------------------------------------------------
@login_required
def dashboard(request):
    wallet=get_wallet(request.user)
    tickets=Ticket.objects.filter(user=request.user).select_related('route').order_by('-purchased_at')[:5]
    transactions=Transaction.objects.filter(user=request.user)[:5]
    total_rides=Ticket.objects.filter(user=request.user,status='used').count()
    active_count=Ticket.objects.filter(user=request.user,status='active').count()
    total_spent=Transaction.objects.filter(user=request.user,transaction_type='purchase').aggregate(s=Sum('amount'))['s'] or 0
    return render(request,'core/dashboard.html',{'wallet':wallet,'tickets':tickets,'transactions':transactions,
        'total_rides':total_rides,'active_count':active_count,'total_spent':total_spent,'notif_count':unread(request.user)})

@login_required
def routes_view(request):
    routes=Route.objects.filter(is_active=True).order_by('transport_type','fare')
    tf=request.GET.get('type','')
    if tf: routes=routes.filter(transport_type=tf)
    return render(request,'core/routes.html',{'routes':routes,'filter':tf,
        'wallet':get_wallet(request.user),'notif_count':unread(request.user)})

@login_required
def buy_ticket(request,route_id):
    route=get_object_or_404(Route,id=route_id,is_active=True)
    wallet=get_wallet(request.user)
    return render(request,'core/buy_ticket.html',{'route':route,'wallet':wallet,'notif_count':unread(request.user)})

@login_required
def ticket_detail(request,ticket_id):
    ticket=get_object_or_404(Ticket,id=ticket_id,user=request.user)
    from .qr_utils import generate_ticket_qr
    qr_url = generate_ticket_qr(ticket)
    return render(request,'core/ticket_detail.html',{'ticket':ticket,
        'wallet':get_wallet(request.user),'notif_count':unread(request.user),
        'qr_url': qr_url})

@login_required
def cancel_ticket(request,ticket_id):
    ticket=get_object_or_404(Ticket,id=ticket_id,user=request.user)
    if ticket.status=='active':
        ticket.status='cancelled'; ticket.save()
        wallet=get_wallet(request.user); wallet.balance+=ticket.fare_paid; wallet.save()
        Transaction.objects.create(user=request.user,transaction_type='topup',amount=ticket.fare_paid,
            description=f'Refund: Cancelled {ticket.route.name}',ticket=ticket)
        add_notif(request.user,'Ticket Cancelled',f'₱{ticket.fare_paid} refunded.','↩️')
        messages.success(request,f'Ticket cancelled. ₱{ticket.fare_paid} refunded.')
    else: messages.error(request,'Only active tickets can be cancelled.')
    return redirect('my_tickets')

@login_required
def my_tickets(request):
    sf=request.GET.get('status','')
    tickets=Ticket.objects.filter(user=request.user).select_related('route').order_by('-purchased_at')
    if sf: tickets=tickets.filter(status=sf)
    return render(request,'core/my_tickets.html',{'tickets':tickets,'filter':sf,
        'wallet':get_wallet(request.user),'notif_count':unread(request.user)})

@login_required
def history_view(request):
    transactions=Transaction.objects.filter(user=request.user).select_related('ticket__route')
    return render(request,'core/history.html',{'transactions':transactions,
        'wallet':get_wallet(request.user),'notif_count':unread(request.user)})

@login_required
def notifications_view(request):
    notifs=Notification.objects.filter(user=request.user)
    Notification.objects.filter(user=request.user,is_read=False).update(is_read=True)
    return render(request,'core/notifications.html',{'notifications':notifs,
        'wallet':get_wallet(request.user),'notif_count':0})

@login_required
def profile_view(request):
    profile=get_profile(request.user); wallet=get_wallet(request.user)
    if request.method=='POST':
        action=request.POST.get('action')
        if action=='update_info':
            request.user.first_name=request.POST.get('first_name','')
            request.user.last_name=request.POST.get('last_name','')
            request.user.email=request.POST.get('email','')
            request.user.save()
            profile.phone=request.POST.get('phone',''); profile.address=request.POST.get('address',''); profile.save()
            messages.success(request,'Profile updated!')
        elif action=='change_password':
            old=request.POST.get('old_password'); new=request.POST.get('new_password'); conf=request.POST.get('confirm_password')
            if not request.user.check_password(old): messages.error(request,'Current password incorrect.')
            elif new!=conf: messages.error(request,'Passwords do not match.')
            elif len(new)<6: messages.error(request,'Minimum 6 characters.')
            else:
                request.user.set_password(new); request.user.save()
                update_session_auth_hash(request,request.user)
                add_notif(request.user,'Password Changed','Your password was updated.','🔒')
                messages.success(request,'Password changed!')
        return redirect('profile')
    total_spent=Transaction.objects.filter(user=request.user,transaction_type='purchase').aggregate(s=Sum('amount'))['s'] or 0
    total_rides=Ticket.objects.filter(user=request.user,status='used').count()
    return render(request,'core/profile.html',{'profile':profile,'wallet':wallet,
        'total_spent':total_spent,'total_rides':total_rides,'notif_count':unread(request.user)})

@login_required
def scan_view(request):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Only staff can access this page.')
    scanned_ticket=None; error=None
    if request.method=='POST':
        code=request.POST.get('code','').strip().upper()
        try:
            ticket=Ticket.objects.select_related('route','user').get(ticket_code__icontains=code[:8])
            if ticket.status=='active':
                ticket.status='used'; ticket.used_at=timezone.now(); ticket.save()
                add_notif(ticket.user,'Ticket Used',f'Your ticket for {ticket.route.name} was scanned.','✅')
                scanned_ticket=ticket; messages.success(request,'Ticket validated!')
            elif ticket.status=='used': error='This ticket has already been used.'
            else: error=f'Ticket is {ticket.status}.'
        except Ticket.DoesNotExist: error='No ticket found with that code.'
    return render(request,'core/scan.html',{'scanned_ticket':scanned_ticket,'error':error,
        'wallet':get_wallet(request.user),'notif_count':unread(request.user)})

@login_required
def topup_view(request):
    wallet = get_wallet(request.user)
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            if amount < 50 or amount > 5000:
                messages.error(request, 'Amount must be between ₱50 and ₱5,000.')
            else:
                wallet.balance += amount
                wallet.save()
                Transaction.objects.create(
                    user=request.user,
                    transaction_type='topup',
                    amount=amount,
                    description=f"Wallet top-up via {request.POST.get('method', 'GCash')}"
                )
                add_notif(request.user, 'Wallet Topped Up', f'₱{amount:,.2f} added to your wallet.', '💰')
                messages.success(request, f'₱{amount:,.2f} added to your wallet!')
                return redirect('dashboard')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Invalid amount.')
    return render(request, 'core/topup.html', {
        'wallet': wallet,
        'notif_count': unread(request.user),
    })

# == ADMIN PANEL VIEWS ========================================================

def admin_required(view_func):
    decorated=login_required(user_passes_test(is_admin, login_url='/login/')(view_func))
    return decorated

@admin_required
def admin_dashboard(request):
    total_users=User.objects.filter(is_staff=False).count()
    total_tickets=Ticket.objects.count()
    total_revenue=Transaction.objects.filter(transaction_type='topup').aggregate(s=Sum('amount'))['s'] or 0
    active_routes=Route.objects.filter(is_active=True).count()
    recent_users=User.objects.filter(is_staff=False).order_by('-date_joined')[:5]
    recent_tickets=Ticket.objects.select_related('user','route').order_by('-purchased_at')[:5]
    tickets_by_status=Ticket.objects.values('status').annotate(count=Count('id'))
    routes_usage=Route.objects.annotate(ticket_count=Count('ticket')).order_by('-ticket_count')[:5]
    return render(request,'core/admin/dashboard.html',{
        'total_users':total_users,'total_tickets':total_tickets,
        'total_revenue':total_revenue,'active_routes':active_routes,
        'recent_users':recent_users,'recent_tickets':recent_tickets,
        'tickets_by_status':tickets_by_status,'routes_usage':routes_usage,
    })

# -- Admin: Users -------------------------------------------------------------
@admin_required
def admin_users(request):
    q=request.GET.get('q','')
    status=request.GET.get('status','')
    users=User.objects.filter(is_staff=False).select_related('wallet','profile').order_by('-date_joined')
    if q: users=users.filter(Q(username__icontains=q)|Q(email__icontains=q)|Q(first_name__icontains=q)|Q(last_name__icontains=q))
    if status=='active': users=users.filter(is_active=True)
    elif status=='banned': users=users.filter(profile__is_banned=True)
    return render(request,'core/admin/users.html',{'users':users,'q':q,'status':status})

@admin_required
def admin_user_detail(request,user_id):
    u=get_object_or_404(User,id=user_id,is_staff=False)
    profile=get_profile(u); wallet=get_wallet(u)
    tickets=Ticket.objects.filter(user=u).select_related('route').order_by('-purchased_at')
    transactions=Transaction.objects.filter(user=u).order_by('-created_at')
    total_spent=transactions.filter(transaction_type='purchase').aggregate(s=Sum('amount'))['s'] or 0
    return render(request,'core/admin/user_detail.html',{'u':u,'profile':profile,'wallet':wallet,
        'tickets':tickets,'transactions':transactions,'total_spent':total_spent})

@admin_required
def admin_user_edit(request,user_id):
    u=get_object_or_404(User,id=user_id,is_staff=False)
    profile=get_profile(u); wallet=get_wallet(u)
    if request.method=='POST':
        action=request.POST.get('action')
        if action=='edit_info':
            u.first_name=request.POST.get('first_name','')
            u.last_name=request.POST.get('last_name','')
            u.email=request.POST.get('email','')
            u.is_active=request.POST.get('is_active')=='on'
            u.save()
            profile.phone=request.POST.get('phone','')
            profile.address=request.POST.get('address','')
            profile.save()
            messages.success(request,f'User {u.username} updated!')
        elif action=='adjust_wallet':
            try:
                amount=Decimal(request.POST.get('amount','0'))
                op=request.POST.get('operation','add')
                reason=request.POST.get('reason','Admin adjustment')
                if op=='add':
                    wallet.balance+=amount; wallet.save()
                    Transaction.objects.create(user=u,transaction_type='topup',amount=amount,description=f'Admin top-up: {reason}')
                    add_notif(u,'Wallet Adjusted',f'Admin added ₱{amount:,.2f} to your wallet.','💰')
                    messages.success(request,f'Added ₱{amount:,.2f} to wallet.')
                else:
                    if wallet.balance>=amount:
                        wallet.balance-=amount; wallet.save()
                        Transaction.objects.create(user=u,transaction_type='purchase',amount=amount,description=f'Admin deduction: {reason}')
                        add_notif(u,'Wallet Adjusted',f'Admin deducted ₱{amount:,.2f} from your wallet.','💰')
                        messages.success(request,f'Deducted ₱{amount:,.2f} from wallet.')
                    else: messages.error(request,'Insufficient wallet balance.')
            except (InvalidOperation,ValueError): messages.error(request,'Invalid amount.')
        elif action=='reset_password':
            new_pw=request.POST.get('new_password','')
            if len(new_pw)<6: messages.error(request,'Minimum 6 characters.')
            else:
                u.set_password(new_pw); u.save()
                add_notif(u,'Password Reset','An admin has reset your password. Please log in again.','🔒')
                messages.success(request,f'Password for {u.username} reset.')
        elif action=='ban_user':
            reason=request.POST.get('ban_reason','Violated terms')
            profile.is_banned=True; profile.ban_reason=reason; profile.save()
            u.is_active=False; u.save()
            add_notif(u,'Account Banned',f'Your account has been banned: {reason}','🚫')
            messages.success(request,f'User {u.username} banned.')
        elif action=='unban_user':
            profile.is_banned=False; profile.ban_reason=''; profile.save()
            u.is_active=True; u.save()
            add_notif(u,'Account Reinstated','Your account has been reinstated by an admin.','✅')
            messages.success(request,f'User {u.username} unbanned.')
        elif action=='send_notification':
            title=request.POST.get('notif_title','Message from Admin')
            msg=request.POST.get('notif_message','')
            if msg: add_notif(u,title,msg,'📢'); messages.success(request,'Notification sent.')
        return redirect('admin_user_edit',user_id=user_id)
    return render(request,'core/admin/user_edit.html',{'u':u,'profile':profile,'wallet':wallet})

@admin_required
def admin_delete_user(request,user_id):
    u=get_object_or_404(User,id=user_id,is_staff=False)
    if request.method=='POST':
        username=u.username; u.delete()
        messages.success(request,f'User {username} deleted.')
        return redirect('admin_users')
    return render(request,'core/admin/confirm_delete.html',{'obj':u,'type':'user','cancel_url':f'/admin-panel/users/{user_id}/edit/'})

# -- Admin: Routes ------------------------------------------------------------
@admin_required
def admin_routes(request):
    routes=Route.objects.annotate(ticket_count=Count('ticket')).order_by('transport_type')
    return render(request,'core/admin/routes.html',{'routes':routes})

@admin_required
def admin_route_add(request):
    if request.method=='POST':
        Route.objects.create(
            name=request.POST.get('name'),origin=request.POST.get('origin'),
            destination=request.POST.get('destination'),transport_type=request.POST.get('transport_type'),
            fare=Decimal(request.POST.get('fare','0')),duration_minutes=int(request.POST.get('duration_minutes',30)),
            is_active=request.POST.get('is_active')=='on')
        messages.success(request,'Route added!'); return redirect('admin_routes')
    return render(request,'core/admin/route_form.html',{'route':None,'title':'Add Route'})

@admin_required
def admin_route_edit(request,route_id):
    route=get_object_or_404(Route,id=route_id)
    if request.method=='POST':
        route.name=request.POST.get('name'); route.origin=request.POST.get('origin')
        route.destination=request.POST.get('destination'); route.transport_type=request.POST.get('transport_type')
        route.fare=Decimal(request.POST.get('fare','0')); route.duration_minutes=int(request.POST.get('duration_minutes',30))
        route.is_active=request.POST.get('is_active')=='on'; route.save()
        messages.success(request,'Route updated!'); return redirect('admin_routes')
    return render(request,'core/admin/route_form.html',{'route':route,'title':'Edit Route'})

@admin_required
def admin_delete_route(request,route_id):
    route=get_object_or_404(Route,id=route_id)
    if request.method=='POST':
        name=route.name; route.delete()
        messages.success(request,f'Route "{name}" deleted.'); return redirect('admin_routes')
    return render(request,'core/admin/confirm_delete.html',{'obj':route,'type':'route','cancel_url':'/admin-panel/routes/'})

# -- Admin: Tickets -----------------------------------------------------------
@admin_required
def admin_tickets(request):
    sf=request.GET.get('status',''); q=request.GET.get('q','')
    tickets=Ticket.objects.select_related('user','route').order_by('-purchased_at')
    if sf: tickets=tickets.filter(status=sf)
    if q: tickets=tickets.filter(Q(user__username__icontains=q)|Q(route__name__icontains=q))
    return render(request,'core/admin/tickets.html',{'tickets':tickets,'filter':sf,'q':q})

@admin_required
def admin_ticket_edit(request,ticket_id):
    ticket=get_object_or_404(Ticket,id=ticket_id)
    if request.method=='POST':
        ticket.status=request.POST.get('status'); ticket.save()
        messages.success(request,'Ticket status updated.'); return redirect('admin_tickets')
    return render(request,'core/admin/ticket_edit.html',{'ticket':ticket})

# -- Admin: Transactions ------------------------------------------------------
@admin_required
def admin_transactions(request):
    q=request.GET.get('q',''); tf=request.GET.get('type','')
    txs=Transaction.objects.select_related('user','ticket__route').order_by('-created_at')
    if q: txs=txs.filter(Q(user__username__icontains=q)|Q(description__icontains=q))
    if tf: txs=txs.filter(transaction_type=tf)
    total=txs.aggregate(s=Sum('amount'))['s'] or 0
    return render(request,'core/admin/transactions.html',{'transactions':txs,'q':q,'filter':tf,'total':total})