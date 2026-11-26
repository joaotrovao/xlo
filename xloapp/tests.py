from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Compra, Item, Utilizador


class RegistrationTests(TestCase):
    def test_password_is_hashed_and_user_can_log_in_again(self):
        self.client.post(reverse('criarconta'), {
            'username': 'ana', 'iban': 'PT50000000000000000000000',
            'password': 'uma-password-segura-123', 'foto': 'https://example.com/a.jpg',
            'cidade': 'Coimbra', 'pais': 'Portugal',
        })
        user = Utilizador.objects.get(username='ana')
        self.assertNotEqual(user.password, 'uma-password-segura-123')
        self.assertTrue(user.check_password('uma-password-segura-123'))

        self.client.get(reverse('logout'))
        response = self.client.post(reverse('login'), {'username': 'ana', 'password': 'uma-password-segura-123'})
        self.assertRedirects(response, reverse('home'))


class MarketplaceTests(TestCase):
    def setUp(self):
        self.seller = Utilizador.objects.create_user('seller', iban='PT1', password='pw-seller-123')
        self.buyer = Utilizador.objects.create_user('buyer', iban='PT2', password='pw-buyer-123')
        self.sub = Categoria.objects.create(sub='Sapatos', cat='Roupa')
        self.item = Item.objects.create(
            nome='Sapatos', preco=24, descricao='Bons', valido=True,
            utilizador_username=self.seller, categoria_sub=self.sub,
        )

    def test_pages_require_login(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)

    def test_buyer_sees_buy_button_seller_does_not(self):
        url = reverse('view_item', args=[self.item.ref])
        buy_url = reverse('compra', args=[self.item.ref])

        self.client.force_login(self.buyer)
        self.assertContains(self.client.get(url), buy_url)

        self.client.force_login(self.seller)
        self.assertNotContains(self.client.get(url), buy_url)

    def test_buying_an_item(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse('compra', args=[self.item.ref]))
        self.assertTrue(Compra.objects.filter(item_ref=self.item, utilizador_username=self.buyer).exists())
        # Sold items disappear from the home page
        self.assertNotContains(self.client.get(reverse('home')), reverse('view_item', args=[self.item.ref]))

    def test_cannot_buy_own_item(self):
        self.client.force_login(self.seller)
        self.client.post(reverse('compra', args=[self.item.ref]))
        self.assertFalse(Compra.objects.exists())

    def test_cannot_buy_item_twice(self):
        Compra.objects.create(item_ref=self.item, utilizador_username=self.buyer)
        other = Utilizador.objects.create_user('other', iban='PT3', password='pw-other-123')
        self.client.force_login(other)
        self.client.post(reverse('compra', args=[self.item.ref]))
        self.assertEqual(Compra.objects.count(), 1)

    def test_cannot_buy_unapproved_item(self):
        self.item.valido = False
        self.item.save()
        self.client.force_login(self.buyer)
        self.client.post(reverse('compra', args=[self.item.ref]))
        self.assertFalse(Compra.objects.exists())

    def test_unapproved_item_hidden_from_other_users(self):
        self.item.valido = False
        self.item.save()
        url = reverse('view_item', args=[self.item.ref])
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_new_items_start_unapproved(self):
        self.client.force_login(self.seller)
        self.client.post(reverse('add_item_view', args=[self.seller.id]), {
            'nome': 'Casaco', 'preco': 30, 'descricao': 'Quente', 'categoria_sub': 'Sapatos',
            'fotos': 'https://example.com/1.jpg, https://example.com/2.jpg',
        })
        novo = Item.objects.get(nome='Casaco')
        self.assertFalse(novo.valido)
        self.assertEqual(novo.utilizador_username, self.seller)
        self.assertEqual(novo.foto_set.count(), 2)

    def test_normal_users_have_no_admin_permissions(self):
        self.assertFalse(self.buyer.has_perm('xloapp.delete_item'))
        self.assertFalse(self.buyer.is_staff)
