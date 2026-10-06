import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/providers.dart';
import '../../core/ui/widgets.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _email = TextEditingController(), _password = TextEditingController();
  bool _busy = false;
  String? _error;

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(authProvider.notifier).login(_email.text, _password.text);
    } catch (e) {
      if (mounted) setState(() => _error = errorText(context, e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final expired = ref.watch(authProvider).value?.sessionExpired ?? false;
    return Scaffold(
      body: SafeArea(
        child: ListView(padding: const EdgeInsets.all(24), children: [
          const SizedBox(height: 32),
          Icon(Icons.savings, size: 64, color: Theme.of(context).colorScheme.primary),
          Text(l.appTitle, textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineMedium),
          Text(l.signInTitle, textAlign: TextAlign.center),
          const SizedBox(height: 24),
          if (expired) Card(color: Colors.amber.shade100, child: Padding(padding: const EdgeInsets.all(12), child: Text(l.sessionExpired))),
          TextField(key: const Key('login-email'), controller: _email, decoration: InputDecoration(labelText: l.email), keyboardType: TextInputType.emailAddress, autofillHints: const [AutofillHints.email]),
          TextField(key: const Key('login-password'), controller: _password, decoration: InputDecoration(labelText: l.password), obscureText: true, onSubmitted: (_) => _submit()),
          if (_error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, key: const Key('login-error'), style: TextStyle(color: Theme.of(context).colorScheme.error))),
          const SizedBox(height: 24),
          FilledButton(key: const Key('login-submit'), onPressed: _busy ? null : _submit, child: _busy ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2)) : Text(l.signIn)),
          TextButton(
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const RegisterScreen())),
            child: Text(l.noAccount),
          ),
        ]),
      ),
    );
  }
}

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});
  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _name = TextEditingController(), _email = TextEditingController(), _phone = TextEditingController(), _pw = TextEditingController();
  String _lang = 'en';
  bool _busy = false;
  String? _error;

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(authProvider.notifier).register({
        'full_name': _name.text.trim(),
        'email': _email.text.trim(),
        'phone_number': _phone.text.trim(),
        'password': _pw.text,
        'preferred_language': _lang,
      });
      if (mounted) Navigator.of(context).popUntil((r) => r.isFirst);
    } catch (e) {
      if (mounted) setState(() => _error = errorText(context, e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    return Scaffold(
      appBar: AppBar(title: Text(l.registerTitle)),
      body: ListView(padding: const EdgeInsets.all(24), children: [
        TextField(controller: _name, decoration: InputDecoration(labelText: l.fullName)),
        TextField(controller: _email, decoration: InputDecoration(labelText: l.email), keyboardType: TextInputType.emailAddress),
        TextField(controller: _phone, decoration: InputDecoration(labelText: l.phone), keyboardType: TextInputType.phone),
        TextField(controller: _pw, decoration: InputDecoration(labelText: l.password, helperText: l.passwordHelp), obscureText: true),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          initialValue: _lang,
          decoration: InputDecoration(labelText: l.language),
          items: const [
            DropdownMenuItem(value: 'en', child: Text('English')),
            DropdownMenuItem(value: 'lg', child: Text('Luganda')),
            DropdownMenuItem(value: 'sw', child: Text('Kiswahili')),
          ],
          onChanged: (v) => setState(() => _lang = v ?? 'en'),
        ),
        if (_error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
        const SizedBox(height: 24),
        FilledButton(onPressed: _busy ? null : _submit, child: Text(l.register)),
      ]),
    );
  }
}
