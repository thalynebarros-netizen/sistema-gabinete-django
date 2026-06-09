from django.db import models

from contacts.models import Contact


class MobilizationGroup(models.Model):
    name = models.CharField("nome", max_length=240)
    city = models.CharField("cidade", max_length=160, blank=True, db_index=True)
    kind = models.CharField("tipo", max_length=120)
    member_count = models.PositiveIntegerField("quantidade de membros", default=0)
    leader = models.ForeignKey(
        Contact,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="led_groups",
        verbose_name="liderança",
    )
    notes = models.TextField("observações", blank=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "grupo de mobilização"
        verbose_name_plural = "grupos de mobilização"
        ordering = ("city", "name")

    def __str__(self):
        return self.name
