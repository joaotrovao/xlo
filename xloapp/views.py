from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CompraForm, ItemForm, RegistrationForm
from .models import Categoria, Compra, Foto, Item, Utilizador


def get_categorias_with_subs():
    """Categories with their sub-categories, used by the sidebar on every page."""
    categorias_with_subs = []
    for categoria in Categoria.objects.values('cat').distinct().order_by('cat'):
        cat = categoria['cat']
        categorias_with_subs.append({'cat': cat, 'sub': Categoria.objects.filter(cat=cat)})
    return categorias_with_subs


def sold_item_refs():
    """Subquery matching items that already have a purchase (Compra)."""
    return Compra.objects.filter(item_ref=OuterRef('ref')).values('item_ref')


def items_for_sale(user, **filters):
    """Approved, unsold items listed by other users, newest first."""
    return (
        Item.objects.filter(valido=True, **filters)
        .exclude(utilizador_username=user.id)
        .exclude(ref__in=sold_item_refs())
        .order_by('-ref')
    )


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('home')

        return render(request, 'xloapp/login.html', {'error_message': 'Invalid username or password.'})

    return render(request, 'xloapp/login.html')


def criar_conta(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()

    return render(request, 'xloapp/criar_conta.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    context = {
        'categorias': get_categorias_with_subs(),
        'items': items_for_sale(request.user),
    }
    return render(request, 'xloapp/home.html', context)


@login_required
def home_cat(request, cat):
    context = {
        'categorias': get_categorias_with_subs(),
        'items': items_for_sale(request.user, categoria_sub__cat=cat),
    }
    return render(request, 'xloapp/home.html', context)


@login_required
def home_sub(request, cat, sub):
    context = {
        'categorias': get_categorias_with_subs(),
        'items': items_for_sale(request.user, categoria_sub__cat=cat, categoria_sub__sub=sub),
    }
    return render(request, 'xloapp/home.html', context)


@login_required
def view_item(request, ref):
    item = get_object_or_404(Item, ref=ref)
    is_seller = item.utilizador_username_id == request.user.id

    # Items not yet approved by an admin are only visible to their seller (and admins)
    if not item.valido and not (is_seller or request.user.is_superuser):
        raise Http404

    context = {
        'categorias': get_categorias_with_subs(),
        'item': item,
        'fotos': Foto.objects.filter(item_ref=ref),
        'seller': item.utilizador_username,
        'compra_exists': Compra.objects.filter(item_ref_id=ref).exists(),
    }
    return render(request, 'xloapp/view_item.html', context)


@login_required
def view_perfil(request, utilizador_username_id):
    user_perfil = get_object_or_404(Utilizador, id=utilizador_username_id)
    own_items = Item.objects.filter(valido=True, utilizador_username_id=user_perfil.id).order_by('-ref')

    context = {
        'categorias': get_categorias_with_subs(),
        'items': own_items.exclude(ref__in=sold_item_refs()),
        'items_sold': own_items.filter(ref__in=sold_item_refs()),
        'user_perfil': user_perfil,
    }
    return render(request, 'xloapp/view_perfil.html', context)


@login_required
def add_item_view(request, utilizador_username_id):
    # Users can only add items to their own profile
    if utilizador_username_id != request.user.id:
        return redirect('add_item_view', utilizador_username_id=request.user.id)

    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.valido = False  # Must be approved by an admin before it is listed
            item.utilizador_username = request.user
            item.save()

            for url in form.cleaned_data.get('fotos', []):
                Foto.objects.create(url=url, item_ref=item, valido=False)

            return redirect('view_perfil', utilizador_username_id=request.user.id)
    else:
        form = ItemForm()

    return render(request, 'xloapp/add_item.html', {'form': form, 'categorias': get_categorias_with_subs()})


@login_required
def compra(request, ref):
    item = get_object_or_404(Item, ref=ref)

    # Only approved items from other users that haven't been sold can be bought
    already_sold = Compra.objects.filter(item_ref=item).exists()
    if not item.valido or item.utilizador_username_id == request.user.id or already_sold:
        return redirect('view_item', ref=item.ref)

    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            nova_compra = form.save(commit=False)
            nova_compra.data = timezone.now()
            nova_compra.item_ref = item
            nova_compra.utilizador_username = request.user
            nova_compra.save()
            return redirect('home')
    else:
        form = CompraForm()

    context = {
        'form': form,
        'categorias': get_categorias_with_subs(),
        'item': item,
        'user_perfil': item.utilizador_username,
    }
    return render(request, 'xloapp/comprasuccess.html', context)
