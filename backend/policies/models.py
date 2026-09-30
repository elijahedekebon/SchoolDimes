from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ProductCategory(models.Model):
    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="product_categories")
    name = models.CharField(max_length=100)
    is_unhealthy = models.BooleanField(
        default=False, help_text="Counts toward the 'unhealthy share of spend' nutrition flag in analytics."
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Product categories"
        constraints = [models.UniqueConstraint(fields=["school", "name"], name="unique_category_name_per_school")]

    def __str__(self):
        return self.name


class Product(models.Model):
    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="products")
    merchant = models.ForeignKey(
        "merchants.Merchant", on_delete=models.CASCADE, null=True, blank=True, related_name="products",
        help_text="Null = sold by the school canteen (Section G).",
    )
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name="products")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.price})"


class Policy(models.Model):
    """
    Spending controls. One row per school with student=null is the school
    default; a row with a student is that student's override. Resolution
    (policies.services.get_effective_policy): overrides can only TIGHTEN --
    caps take the smaller value, blocks are unioned, allow-lists intersected,
    p2p needs both to allow it. Null cap / p2p_enabled = "inherit/no limit".
    Supersedes the Part 1 School.policy_defaults JSON (kept, no longer read).
    """

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="policies")
    student = models.OneToOneField(
        "students.Student", on_delete=models.CASCADE, null=True, blank=True, related_name="policy_override"
    )
    daily_spend_cap = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    weekly_spend_cap = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    per_transaction_cap = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    p2p_daily_cap = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    p2p_enabled = models.BooleanField(null=True, blank=True, help_text=_("Null = inherit (school default null = enabled)."))
    low_balance_threshold = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    blocked_categories = models.ManyToManyField(ProductCategory, blank=True, related_name="+")
    allowed_categories = models.ManyToManyField(
        ProductCategory, blank=True, related_name="+", help_text="Empty = every category allowed."
    )
    blocked_items = models.ManyToManyField(Product, blank=True, related_name="+")
    blocked_merchants = models.ManyToManyField("merchants.Merchant", blank=True, related_name="+")
    allowed_merchants = models.ManyToManyField(
        "merchants.Merchant", blank=True, related_name="+", help_text="Empty = every approved merchant allowed."
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Policies"
        ordering = ["school", "student", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["school"], condition=models.Q(student__isnull=True), name="one_default_policy_per_school"
            ),
        ]

    def __str__(self):
        return f"Policy({self.school_id}, student={self.student_id})"
