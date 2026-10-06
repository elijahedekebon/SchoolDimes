import 'package:drift/drift.dart' hide Column;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/services.dart';
import '../../app/session.dart';
import '../../core/db/database.dart';
import '../../core/money/money.dart';
import '../../core/ui/widgets.dart';
import '../policy/policy_engine.dart';
import 'card_flow.dart';
import 'receipt_page.dart';
import 'sale_service.dart';

final _productsProvider = StreamProvider<List<Product>>((ref) {
  final db = ref.watch(sessionProvider).requireValue.db;
  return (db.select(db.products)
        ..where((p) => p.active.equals(true))
        ..orderBy([(p) => OrderingTerm.asc(p.categoryName), (p) => OrderingTerm.asc(p.name)]))
      .watch();
});

class CartLine {
  CartLine({this.product, required this.description, required this.unitPrice, this.categoryId, this.quantity = 1});
  final Product? product;
  final String description;
  final Money unitPrice;
  final int? categoryId;
  int quantity;
  Money get total => unitPrice * quantity;
  SaleLine toSaleLine() => SaleLine(productId: product?.id, categoryId: product?.categoryId ?? categoryId, quantity: quantity, unitPrice: unitPrice, description: description);
}

class SaleScreen extends ConsumerStatefulWidget {
  const SaleScreen({super.key});
  @override
  ConsumerState<SaleScreen> createState() => _SaleScreenState();
}

class _SaleScreenState extends ConsumerState<SaleScreen> {
  final List<CartLine> _cart = [];
  String _search = '';
  String? _category;
  bool _busy = false;

  Money get _total => Money.sum(_cart.map((l) => l.total));

  void _add(Product p) => setState(() {
        final existing = _cart.where((l) => l.product?.id == p.id).firstOrNull;
        if (existing != null) {
          existing.quantity++;
        } else {
          _cart.add(CartLine(product: p, description: p.name, unitPrice: Money(p.priceCents)));
        }
      });

  Future<void> _customAmount() async {
    final l = context.l;
    final desc = TextEditingController(), amount = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(l.customAmount),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(key: const Key('custom-desc'), controller: desc, decoration: InputDecoration(labelText: l.customAmountDescription)),
          TextField(key: const Key('custom-amount'), controller: amount, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: InputDecoration(labelText: l.amountUgx)),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)),
          FilledButton(key: const Key('custom-add'), onPressed: () => Navigator.pop(c, true), child: Text(l.add)),
        ],
      ),
    );
    final m = Money.tryParse(amount.text);
    if (ok == true && m != null && m.isPositive) {
      setState(() => _cart.add(CartLine(description: desc.text.trim().isEmpty ? l.customAmount : desc.text.trim(), unitPrice: m)));
    }
  }

  Future<void> _charge() async {
    final l = context.l;
    if (_cart.isEmpty || _busy) return;
    final total = _total;
    final card = await CardTapPage.open(context, title: l.charge(total.format()), subtitle: total.format());
    if (card == null || !mounted) return;
    final sales = ref.read(saleServiceProvider);
    final lines = [for (final c in _cart) c.toSaleLine()];
    final violations = await sales.check(card, total, lines);
    if (!mounted) return;
    if (violations.isNotEmpty) {
      await _refused(violations.first, [for (final v in violations) reasonText(l, v)]);
      return;
    }
    final state = await sales.cards.stateOf(card);
    if (!mounted) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(l.confirmSale),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('${l.student}: ${card.displayName}', style: Theme.of(c).textTheme.titleMedium),
          Text('${l.total}: ${total.format()}', style: Theme.of(c).textTheme.headlineSmall),
          Text('${l.balanceAfter}: ${(state.balance - total).format()} (${l.estimated})'),
          const SizedBox(height: 12),
          Text(l.voidHint, style: Theme.of(c).textTheme.bodySmall),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)),
          FilledButton(key: const Key('confirm-sale'), onPressed: () => Navigator.pop(c, true), child: Text(l.confirm)),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _busy = true);
    try {
      final online = ref.read(statusProvider).value?.online ?? false;
      final outcome = await sales.commit(card, total, lines, online: online && !ref.read(syncEngineProvider).backingOff);
      if (!mounted) return;
      if (outcome.refused) {
        await _refused(outcome.code ?? 'error', [outcome.detail ?? reasonText(l, outcome.code)]);
        return;
      }
      if (outcome.channel == SaleChannel.offline) ref.read(syncControllerProvider).nudge();
      final cartCopy = List<CartLine>.of(_cart);
      setState(() => _cart.clear());
      await Navigator.of(context).push(MaterialPageRoute(builder: (_) => ReceiptPage(lines: cartCopy, total: total, studentName: card.displayName, outcome: outcome)));
    } on DeviceRevoked {
      await ref.read(sessionProvider.notifier).markRevoked();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _refused(String code, List<String> messages) => showDialog<void>(
        context: context,
        builder: (c) => AlertDialog(
          icon: const Icon(Icons.block, color: Colors.red, size: 48),
          title: Text(context.l.refusedTitle),
          content: Column(mainAxisSize: MainAxisSize.min, children: [for (final m in messages) Text(m, key: const Key('refusal-reason'), textAlign: TextAlign.center)]),
          actions: [FilledButton(onPressed: () => Navigator.pop(c), child: Text(context.l.back))],
        ),
      );

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final products = ref.watch(_productsProvider).value ?? const <Product>[];
    final categories = {for (final p in products) p.categoryName}.toList();
    final shown = products
        .where((p) => (_category == null || p.categoryName == _category) && (_search.isEmpty || p.name.toLowerCase().contains(_search.toLowerCase())))
        .toList();
    return Column(children: [
      const StatusBar(),
      Padding(
        padding: const EdgeInsets.fromLTRB(8, 8, 8, 0),
        child: TextField(
          key: const Key('product-search'),
          decoration: InputDecoration(prefixIcon: const Icon(Icons.search), hintText: l.search, isDense: true, border: const OutlineInputBorder()),
          onChanged: (v) => setState(() => _search = v),
        ),
      ),
      SizedBox(
        height: 48,
        child: ListView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.symmetric(horizontal: 8), children: [
          Padding(padding: const EdgeInsets.all(4), child: ChoiceChip(label: Text(l.allCategories), selected: _category == null, onSelected: (_) => setState(() => _category = null))),
          for (final c in categories)
            Padding(padding: const EdgeInsets.all(4), child: ChoiceChip(label: Text(c), selected: _category == c, onSelected: (_) => setState(() => _category = c))),
        ]),
      ),
      Expanded(
        child: GridView.builder(
          padding: const EdgeInsets.all(8),
          gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(maxCrossAxisExtent: 160, childAspectRatio: 1.3, mainAxisSpacing: 8, crossAxisSpacing: 8),
          itemCount: shown.length + 1,
          itemBuilder: (_, i) => i == shown.length
              ? OutlinedButton.icon(key: const Key('custom-amount-button'), onPressed: _customAmount, icon: const Icon(Icons.edit), label: Text(l.customAmount, textAlign: TextAlign.center))
              : Card(
                  key: Key('product-${shown[i].id}'),
                  child: InkWell(
                    onTap: () => _add(shown[i]),
                    child: Padding(
                      padding: const EdgeInsets.all(8),
                      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                        Text(shown[i].name, textAlign: TextAlign.center, maxLines: 2, style: const TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text(Money(shown[i].priceCents).format()),
                      ]),
                    ),
                  ),
                ),
        ),
      ),
      _CartPanel(cart: _cart, total: _total, busy: _busy, onChanged: () => setState(() {}), onClear: () => setState(_cart.clear), onCharge: _charge),
    ]);
  }
}

class _CartPanel extends StatelessWidget {
  const _CartPanel({required this.cart, required this.total, required this.busy, required this.onChanged, required this.onClear, required this.onCharge});
  final List<CartLine> cart;
  final Money total;
  final bool busy;
  final VoidCallback onChanged, onClear, onCharge;

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    return Material(
      elevation: 8,
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          if (cart.isEmpty)
            Padding(padding: const EdgeInsets.all(8), child: Text(l.emptyCart))
          else
            ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 160),
              child: ListView(shrinkWrap: true, children: [
                for (final line in cart)
                  ListTile(
                    dense: true,
                    title: Text(line.description),
                    subtitle: Text('${line.quantity} × ${line.unitPrice.format()}'),
                    trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                      IconButton(icon: const Icon(Icons.remove_circle_outline), onPressed: () {
                        line.quantity > 1 ? line.quantity-- : cart.remove(line);
                        onChanged();
                      }),
                      IconButton(icon: const Icon(Icons.add_circle_outline), onPressed: () {
                        line.quantity++;
                        onChanged();
                      }),
                    ]),
                  ),
              ]),
            ),
          Row(children: [
            TextButton(onPressed: cart.isEmpty ? null : onClear, child: Text(l.clear)),
            // the total shrinks to fit narrow terminals instead of overflowing
            Expanded(
              child: FittedBox(
                fit: BoxFit.scaleDown,
                alignment: Alignment.centerRight,
                child: Text.rich(TextSpan(children: [
                  TextSpan(text: '${l.total}: ', style: Theme.of(context).textTheme.titleMedium),
                  TextSpan(text: total.format(), style: Theme.of(context).textTheme.titleLarge),
                ])),
              ),
            ),
            // keyed copy of the total for tests / accessibility
            Offstage(child: Text(total.format(), key: const Key('cart-total'))),
            const SizedBox(width: 8),
            FilledButton.icon(
              key: const Key('charge'),
              onPressed: cart.isEmpty || busy ? null : onCharge,
              icon: busy ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.contactless),
              label: Text(l.chargeButton),
            ),
          ]),
        ]),
      ),
    );
  }
}
