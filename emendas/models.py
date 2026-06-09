from django.db import models


class Emenda(models.Model):
    beneficiary = models.CharField("beneficiário", max_length=240)
    city = models.CharField("cidade", max_length=160, blank=True, db_index=True)
    year = models.PositiveSmallIntegerField("ano")
    ministry = models.CharField("ministério", max_length=160, blank=True)
    value_destined = models.DecimalField(
        "valor destinado",
        decimal_places=2,
        max_digits=14,
    )
    value_paid = models.DecimalField(
        "valor pago",
        decimal_places=2,
        default=0,
        max_digits=14,
    )
    status = models.CharField("situação", max_length=180, blank=True)
    object = models.TextField("objeto", blank=True)
    source = models.CharField("fonte", max_length=180, blank=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "emenda"
        verbose_name_plural = "emendas"
        ordering = ("-year", "city", "beneficiary")

    def __str__(self):
        return f"{self.beneficiary} - {self.year}"
