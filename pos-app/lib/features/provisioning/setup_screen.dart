import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../../app/session.dart';
import '../../core/config/env.dart';
import '../../core/ui/widgets.dart';
import 'device_config.dart';
import 'provisioning_service.dart';

/// First run (or re-provisioning): scan the dashboard's one-time QR code, or
/// type the token; set the local staff PIN; download the offline cache.
class SetupScreen extends ConsumerStatefulWidget {
  const SetupScreen({super.key, this.reprovision = false});
  final bool reprovision;
  @override
  ConsumerState<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends ConsumerState<SetupScreen> {
  final _url = TextEditingController(text: Env.defaultApiBaseUrl);
  final _token = TextEditingController();
  final _pin = TextEditingController();
  final _pin2 = TextEditingController();
  String? _status;
  String? _error;
  bool _busy = false;

  @override
  void dispose() {
    for (final c in [_url, _token, _pin, _pin2]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _scan() async {
    final raw = await Navigator.of(context).push<String>(MaterialPageRoute(builder: (_) => const _QrScanPage()));
    if (raw == null || !mounted) return;
    final code = ProvisioningCode.parse(raw);
    if (code == null) {
      setState(() => _error = context.l.errQrInvalid);
      return;
    }
    setState(() {
      _url.text = code.apiBaseUrl;
      _token.text = code.deviceToken;
      _error = null;
    });
  }

  Future<void> _provision() async {
    final l = context.l;
    final pinRequired = !widget.reprovision || _pin.text.isNotEmpty;
    if (pinRequired && (!RegExp(r'^\d{4,8}$').hasMatch(_pin.text) || _pin.text != _pin2.text)) {
      setState(() => _error = l.adminPinMismatch);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
      _status = l.provisioning;
    });
    try {
      // registers the device and downloads cards/products before returning
      await ref.read(sessionProvider.notifier).provision(baseUrl: _url.text, token: _token.text, adminPin: _pin.text);
      if (mounted && widget.reprovision) Navigator.of(context).popUntil((r) => r.isFirst);
    } on ProvisioningError catch (e) {
      setState(() => _error = switch (e.code) {
            'invalid_token' => l.errInvalidToken,
            'unreachable' => l.errUnreachable,
            'unsynced_other_device' => l.errUnsyncedOtherDevice,
            'https_required' => l.errHttpsRequired,
            _ => l.error(e.detail ?? e.code),
          });
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _status = null;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    return Scaffold(
      appBar: AppBar(title: Text(l.setupTitle)),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Text(l.setupIntro),
        const SizedBox(height: 16),
        FilledButton.icon(key: const Key('scan-qr'), onPressed: _busy ? null : _scan, icon: const Icon(Icons.qr_code_scanner), label: Text(l.scanQr)),
        const SizedBox(height: 24),
        Text(l.enterManually, style: Theme.of(context).textTheme.titleSmall),
        if (Env.isDev)
          TextField(key: const Key('setup-url'), controller: _url, decoration: InputDecoration(labelText: l.apiBaseUrl, helperText: l.apiBaseUrlHelp), keyboardType: TextInputType.url),
        TextField(key: const Key('setup-token'), controller: _token, decoration: InputDecoration(labelText: l.deviceToken), autocorrect: false, enableSuggestions: false),
        const SizedBox(height: 16),
        TextField(key: const Key('setup-pin'), controller: _pin, decoration: InputDecoration(labelText: l.adminPin, helperText: l.adminPinHelp), keyboardType: TextInputType.number, obscureText: true),
        TextField(key: const Key('setup-pin2'), controller: _pin2, decoration: InputDecoration(labelText: l.adminPinRepeat), keyboardType: TextInputType.number, obscureText: true),
        const SizedBox(height: 16),
        if (_error != null) Text(_error!, key: const Key('setup-error'), style: TextStyle(color: Theme.of(context).colorScheme.error)),
        if (_status != null) Padding(padding: const EdgeInsets.all(8), child: Row(children: [const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)), const SizedBox(width: 8), Text(_status!)])),
        FilledButton(key: const Key('setup-submit'), onPressed: _busy ? null : _provision, child: Text(l.provision)),
      ]),
    );
  }
}

class _QrScanPage extends StatefulWidget {
  const _QrScanPage();
  @override
  State<_QrScanPage> createState() => _QrScanPageState();
}

class _QrScanPageState extends State<_QrScanPage> {
  bool _done = false;
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(context.l.scanQr)),
        body: MobileScanner(onDetect: (capture) {
          final raw = capture.barcodes.firstOrNull?.rawValue;
          if (raw != null && !_done) {
            _done = true;
            Navigator.of(context).pop(raw);
          }
        }),
      );
}

/// The server said the token is revoked/invalid: selling is stopped, the
/// unsynced queue is kept, and staff set the device up again.
class RevokedScreen extends StatelessWidget {
  const RevokedScreen({super.key});
  @override
  Widget build(BuildContext context) {
    final l = context.l;
    return Scaffold(
      appBar: AppBar(title: Text(l.revokedTitle)),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          const Icon(Icons.block, size: 96, color: Colors.red),
          const SizedBox(height: 16),
          Text(l.revokedBody, key: const Key('revoked-body'), textAlign: TextAlign.center),
          const SizedBox(height: 24),
          FilledButton(onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const SetupScreen(reprovision: true))), child: Text(l.reprovision)),
        ]),
      ),
    );
  }
}
