import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/providers.dart';
import '../../core/api/parent_api.dart';
import '../../core/ui/widgets.dart';

/// KYC-lite: submit GuardianVerification and see its status. The app
/// enforces nothing itself; it shows what the school decides.
class KycScreen extends ConsumerStatefulWidget {
  const KycScreen({super.key, this.onDone});
  final VoidCallback? onDone;
  @override
  ConsumerState<KycScreen> createState() => _KycScreenState();
}

class _KycScreenState extends ConsumerState<KycScreen> {
  final _name = TextEditingController(), _number = TextEditingController();
  String _doc = 'national_id';

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final api = ref.read(parentApiProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.kycTitle)),
      body: Loader<List<Json>>(
        load: api.verifications,
        builder: (c, rows, reload) {
          final v = rows.isEmpty ? null : rows.first;
          final status = (v?['status'] as String?) ?? 'none';
          final canSubmit = v == null || status == 'rejected';
          return ListView(padding: const EdgeInsets.all(24), children: [
            Card(
              child: ListTile(
                leading: Icon(status == 'verified' ? Icons.verified : Icons.hourglass_top, color: status == 'verified' ? Colors.green : null),
                title: Text(switch (status) { 'pending' => l.kycStatus_pending, 'verified' => l.kycStatus_verified, 'rejected' => l.kycStatus_rejected, _ => l.kycStatus_none }, key: const Key('kyc-status')),
                subtitle: (v?['review_notes'] as String?)?.isNotEmpty == true ? Text(l.kycNotes(v!['review_notes'] as String)) : null,
              ),
            ),
            Text(l.kycLimits, style: Theme.of(context).textTheme.bodySmall),
            if (canSubmit) ...[
              const SizedBox(height: 16),
              Text(l.kycIntro),
              TextField(key: const Key('kyc-name'), controller: _name, decoration: InputDecoration(labelText: l.kycNameOnId)),
              DropdownButtonFormField<String>(
                initialValue: _doc,
                decoration: InputDecoration(labelText: l.kycDocType),
                items: [
                  DropdownMenuItem(value: 'national_id', child: Text(l.kycNationalId)),
                  DropdownMenuItem(value: 'passport', child: Text(l.kycPassport)),
                ],
                onChanged: (x) => setState(() => _doc = x ?? 'national_id'),
              ),
              TextField(key: const Key('kyc-number'), controller: _number, decoration: InputDecoration(labelText: l.kycNumber)),
              const SizedBox(height: 16),
              FilledButton(
                key: const Key('kyc-submit'),
                onPressed: () async {
                  final ok = await guarded(context, () => api.submitVerification({'full_name': _name.text.trim(), 'id_document_type': _doc, 'id_number': _number.text.trim()}));
                  if (ok != null) {
                    reload();
                    widget.onDone?.call();
                  }
                },
                child: Text(l.kycSubmit),
              ),
              if (widget.onDone != null) TextButton(onPressed: widget.onDone, child: Text(l.kycSkip)),
            ],
          ]);
        },
      ),
    );
  }
}
