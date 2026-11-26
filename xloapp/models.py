from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UtilizadorManager(BaseUserManager):
    def create_user(self, username, iban, password=None):
        """
        Create and return a regular user with a username, IBAN and password.
        """
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, iban=iban)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, iban, password=None):
        """
        Create and return a superuser (admin) account.
        """
        user = self.create_user(username, iban=iban, password=password)
        user.is_superuser = True
        user.save(using=self._db)

        return user

class Utilizador(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=512, unique=True)
    iban = models.CharField(max_length=34, null=False)
    foto = models.CharField(max_length=512)
    cidade = models.CharField(max_length=512)
    pais = models.CharField(max_length=512)

    objects = UtilizadorManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['iban']

    def __str__(self):
        return self.username

    @property
    def is_staff(self):
        # Only superusers (admins) can access the Django admin.
        return self.is_superuser

class Categoria(models.Model):
    sub = models.CharField(max_length=512, primary_key=True)
    cat = models.CharField(max_length=512, null=False)
    def __str__(self):
        return self.cat + " | " + self.sub 

class Item(models.Model):
    ref = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=512, null=False)
    preco = models.BigIntegerField(null=False)
    descricao = models.CharField(max_length=512, null=False)
    valido = models.BooleanField(null=False)
    utilizador_username = models.ForeignKey(Utilizador, on_delete=models.CASCADE)
    categoria_sub = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    def __str__(self):
        return self.nome

class Foto(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=512, null=False)
    valido = models.BooleanField(null=False)
    item_ref = models.ForeignKey(Item, on_delete=models.CASCADE, null=False)
    def __str__(self):
        return str(self.item_ref)

class Compra(models.Model):
    idcompra = models.AutoField(primary_key=True)
    data = models.DateTimeField(null=False, default=timezone.now)
    item_ref = models.ForeignKey(Item, on_delete=models.CASCADE)
    utilizador_username = models.ForeignKey(Utilizador, on_delete=models.CASCADE)
    def __str__(self):
        return str(self.idcompra)

class Mensagem(models.Model):
    id = models.BigAutoField(primary_key=True)
    conteudo = models.TextField(null=False)
    envio = models.DateTimeField(null=False, default=timezone.now)
    utilizador_envia = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='mensagens_enviadas')
    utilizador_recebe = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='mensagens_recebidas')
    def __str__(self):
        return self.conteudo
