from django.db.models import signals
from django.dispatch import receiver

from accounts.models import EmailAuthenticatedUser
from .models import CashAccount


@receiver(signals.post_save, sender=EmailAuthenticatedUser)
def create_cashaccount(sender, instance, created, **kwargs):
    """ creates cash account on user creation """
    if created:
        CashAccount.objects.create(title="Cash", user=instance)
        print("Object Created")
    print("Signal hit")
