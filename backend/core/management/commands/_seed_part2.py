"""
Part 2 demo data, called at the end of `manage.py seed_demo`. Safe to
re-run: every object is looked up by a natural key, and every money
movement goes through the real services with a FIXED idempotency key, so a
second run finds the originals and moves nothing.

Device tokens are only ever stored hashed, so on every run the three demo
devices get a fresh token (rotation) and the new raw tokens are printed.
"""
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from accounts.models import User
from disputes.models import Dispute
from disputes.services import raise_dispute
from fees.models import FeeCategory
from merchants.models import Merchant, MerchantStaff
from merchants.services import set_approval
from notifications.services import notify
from payments.models import Contributor, RecurringTopUp, StudentTopUpLink
from payments.services import (
    compute_next_run,
    create_gift_voucher,
    create_topup_link,
    initiate_collection,
    mock_confirm,
)
from policies.models import Policy, Product, ProductCategory
from policies.services import KAMPALA, get_school_policy
from pooled_funds.models import PooledFund
from pooled_funds.services import contribute, create_fund
from pos.models import Device, PosTransaction
from pos.services import record_sale, register_device, rotate_device_token
from tenants.services import get_school_settings
from wallets.services import ensure_student_wallets, get_student_wallet


def _user(email, role, school=None, full_name="", phone=""):
    user, created = User.objects.get_or_create(
        email=email, defaults={"role": role, "school": school, "full_name": full_name, "phone_number": phone})
    if created:
        user.set_password("pw123456")
        user.save()
    return user


def _device(admin, school, name, role, merchant=None):
    device = Device.objects.filter(school=school, device_name=name, status=Device.Status.ACTIVE).first()
    if device is None:
        return register_device(admin, school=school, device_name=name, device_role=role, merchant=merchant)
    return rotate_device_token(admin, device)


def seed_part2(stdout, style, school_a, school_admin, parent1, parent2, students):
    amina, brian, cynthia = students
    mock = settings.AGGREGATOR_MODE == "mock"
    for s in students:
        ensure_student_wallets(s)
    parent1.phone_number = parent1.phone_number or "0772100001"
    parent1.save(update_fields=["phone_number"])
    parent2.phone_number = parent2.phone_number or "0772100002"
    parent2.save(update_fields=["phone_number"])

    # --- staff users -------------------------------------------------------
    _user("canteen@kampaladps.schooldimes.test", User.Role.CANTEEN_STAFF, school_a, "Peter Canteen")
    shop_staff = _user("shop@ntindabookshop.schooldimes.test", User.Role.MERCHANT_STAFF, None, "Ruth Bookshop")

    # --- settings, catalogue, policy --------------------------------------
    get_school_settings(school_a)
    cats = {}
    for name, unhealthy in (("Meals", False), ("Snacks", False), ("Sugary drinks", True), ("Stationery", False)):
        cats[name], _ = ProductCategory.objects.get_or_create(school=school_a, name=name, defaults={"is_unhealthy": unhealthy})
    merchant, _ = Merchant.objects.get_or_create(name="Ntinda Bookshop", defaults={
        "category": "bookshop", "contact_phone": "0772300300", "created_by": school_admin})
    set_approval(school_admin, merchant, "approved")
    MerchantStaff.objects.get_or_create(user=shop_staff, defaults={"merchant": merchant})
    products = {}
    for name, cat, price, m in (
        ("Rice & beans", "Meals", "3000", None), ("Chapati", "Snacks", "500", None), ("Mandazi", "Snacks", "300", None),
        ("Soda", "Sugary drinks", "1500", None), ("Juice", "Sugary drinks", "1000", None),
        ("Exercise book", "Stationery", "1200", merchant), ("Pen", "Stationery", "500", merchant),
    ):
        products[name], _ = Product.objects.get_or_create(
            school=school_a, name=name, defaults={"category": cats[cat], "price": Decimal(price), "merchant": m})

    policy = get_school_policy(school_a)
    policy.daily_spend_cap, policy.per_transaction_cap = Decimal("6000"), Decimal("5000")
    policy.p2p_daily_cap, policy.low_balance_threshold = Decimal("3000"), Decimal("2000")
    policy.save()
    override, _ = Policy.objects.get_or_create(school=school_a, student=amina, defaults={"daily_spend_cap": Decimal("4000")})
    override.blocked_items.add(products["Soda"])
    stdout.write(style.SUCCESS("Catalogue, school policy and Amina's override (Soda blocked) ready"))

    # --- devices -----------------------------------------------------------
    tokens = {
        "canteen": _device(school_admin, school_a, "Demo canteen till", "canteen"),
        "merchant": _device(school_admin, school_a, "Ntinda Bookshop till", "merchant", merchant),
        "attendance": _device(school_admin, school_a, "Main gate", "attendance"),
    }
    canteen_device = tokens["canteen"][0]

    # --- fees -----------------------------------------------------------
    for name, kwargs in (
        ("Exam fee", {"amount_type": "fixed", "fixed_amount": Decimal("6000"), "applicable_classes": ["P4", "P6"]}),
        ("School trip", {"amount_type": "range", "min_amount": Decimal("1000"), "max_amount": Decimal("20000")}),
        ("Uniform", {"amount_type": "fixed", "fixed_amount": Decimal("25000")}),
    ):
        FeeCategory.objects.get_or_create(school=school_a, name=name, defaults=kwargs)

    if mock:
        # --- deposits, gift voucher, contributor link ----------------------
        dep, _ = initiate_collection(purpose="wallet_topup", wallet=get_student_wallet(amina), amount=Decimal("15000"),
                                     channel="momo", payer_phone=parent1.phone_number,
                                     idempotency_key="seed-deposit-amina-1", initiated_by=parent1)
        mock_confirm(dep)
        initiate_collection(purpose="wallet_topup", wallet=get_student_wallet(brian), amount=Decimal("5000"),
                            channel="ussd", payer_phone=parent1.phone_number,
                            idempotency_key="seed-deposit-brian-pending", initiated_by=parent1)
        grandma = Contributor.objects.filter(name="Jjajja Nalongo").first() or Contributor.objects.create(
            name="Jjajja Nalongo", phone_number="0701000222", relationship_label="Grandmother")
        voucher, _ = create_gift_voucher(student=amina, amount=Decimal("5000"), message="Well done in your exams!",
                                         channel="momo", payer_phone=grandma.phone_number,
                                         idempotency_key="seed-gift-amina-1", sender_contributor=grandma)
        mock_confirm(voucher.deposit)

        # --- pooled fund ------------------------------------------------
        fund = PooledFund.objects.filter(school=school_a, title="P4 trip to Entebbe Zoo").first() or create_fund(
            parent1, title="P4 trip to Entebbe Zoo", purpose="Bus hire and zoo tickets", group_label="P4",
            target_amount=Decimal("60000"), deadline=(timezone.now() + timedelta(days=30)).date())
        for key, user, amount in (("seed-pooled-1", parent1, "10000"), ("seed-pooled-2", parent2, "7500")):
            dep, _ = contribute(user, fund, amount=Decimal(amount), channel="momo", payer_phone=user.phone_number,
                                idempotency_key=key)
            mock_confirm(dep)

    link = StudentTopUpLink.objects.filter(student=amina, active=True).first() or create_topup_link(parent1, amina)
    if not RecurringTopUp.objects.filter(parent=parent1, student=brian).exists():
        RecurringTopUp.objects.create(
            school=school_a, parent=parent1, student=brian, wallet=get_student_wallet(brian), amount=Decimal("10000"),
            channel="momo", payer_phone=parent1.phone_number, frequency="weekly", day_of_week=0,
            next_run_at=compute_next_run("weekly", 0, None, timezone.now()))

    # --- past POS sales (idempotent keys) ----------------------------------
    yesterday = (timezone.now() - timedelta(days=1)).astimezone(KAMPALA).replace(hour=10, minute=5, second=0, microsecond=0)
    line = lambda p, q=1: {"product_id": products[p].pk, "quantity": q, "unit_price": str(products[p].price)}  # noqa: E731
    for i, (student, lines, hour) in enumerate((
        (amina, [line("Rice & beans")], 13), (brian, [line("Chapati", 2), line("Juice")], 10),
        (cynthia, [line("Mandazi", 3)], 10), (brian, [line("Rice & beans")], 13),
    ), start=1):
        card = student.cards.filter(status="active").first()
        if card is None:
            continue
        amount = sum(Decimal(l["unit_price"]) * l["quantity"] for l in lines)
        record_sale(canteen_device, {
            "idempotency_key": f"seed-pos-{i}", "card_uid": card.card_uid, "amount": str(amount), "items": lines,
            "device_local_timestamp": yesterday.replace(hour=hour).isoformat(), "pin_verified": True,
        })

    # --- an open dispute ----------------------------------------------------
    disputed = PosTransaction.objects.filter(device=canteen_device, idempotency_key="seed-pos-4").first()
    if disputed and not Dispute.objects.filter(pos_transaction=disputed).exists():
        raise_dispute(parent1, reason_category="duplicate", pos_transaction_id=disputed.pk,
                      description="Brian says he only had lunch once yesterday.")

    if not parent1.notifications.filter(event_type="card_unfrozen").exists():
        notify(parent1, "card_unfrozen", {"student_name": brian.name, "actor_name": "Grace Admin"})

    stdout.write(style.SUCCESS("Part 2 demo data ready (payments, pooled fund, POS sales, dispute, notifications)"))
    stdout.write("")
    stdout.write(style.WARNING("Device tokens (rotated on every run; shown once):"))
    for role, (device, raw) in tokens.items():
        stdout.write(f"  {role:<10} device #{device.pk:<4} {device.device_name:<22} DEVICE_TOKEN={raw}")
    stdout.write(style.WARNING("Contributor top-up link token:"))
    stdout.write(f"  TOPUP_LINK_TOKEN={link.token}")
