import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/providers.dart';
import '../../core/api/parent_api.dart';
import '../../core/ui/widgets.dart';

/// Raise a dispute on a transaction: body = its dispute_target + reason.
Future<bool> showDisputeSheet(BuildContext context, Json target) async =>
    await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _DisputeForm(target: target),
    ) ??
    false;

class _DisputeForm extends ConsumerStatefulWidget {
  const _DisputeForm({required this.target});
  final Json target;
  @override
  ConsumerState<_DisputeForm> createState() => _DisputeFormState();
}

class _DisputeFormState extends ConsumerState<_DisputeForm> {
  String _reason = 'wrong_amount';
  final _note = TextEditingController();

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final reasons = {
      'wrong_amount': l.reason_wrong_amount,
      'not_received': l.reason_not_received,
      'unauthorized': l.reason_unauthorized,
      'duplicate': l.reason_duplicate,
      'other': l.reason_other,
    };
    return Padding(
      padding: EdgeInsets.fromLTRB(16, 0, 16, MediaQuery.of(context).viewInsets.bottom + 16),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(l.disputeReason, style: Theme.of(context).textTheme.titleMedium),
        RadioGroup<String>(
          groupValue: _reason,
          onChanged: (v) => setState(() => _reason = v ?? 'other'),
          child: Column(children: [for (final e in reasons.entries) RadioListTile<String>(key: Key('reason-${e.key}'), value: e.key, title: Text(e.value))]),
        ),
        TextField(controller: _note, decoration: InputDecoration(labelText: l.disputeNote), maxLines: 2),
        const SizedBox(height: 12),
        FilledButton(
          key: const Key('dispute-send'),
          onPressed: () async {
            final r = await guarded(context, () => ref.read(parentApiProvider).raiseDispute({...widget.target, 'reason_category': _reason, 'description': _note.text.trim()}), success: l.disputeSent);
            if (r != null && context.mounted) Navigator.pop(context, true);
          },
          child: Text(l.disputeSend),
        ),
      ]),
    );
  }
}
