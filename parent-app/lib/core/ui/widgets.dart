import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../l10n/gen/app_localizations.dart';
import '../money/money.dart';

extension L10nX on BuildContext {
  AppLocalizations get l => AppLocalizations.of(this);
}

String errorText(BuildContext context, Object e) {
  if (e is ApiException) return e.network ? context.l.networkError : e.message;
  return context.l.error(e.toString());
}

void showMessage(BuildContext context, String text, {bool error = false}) => ScaffoldMessenger.of(context)
  ..clearSnackBars()
  ..showSnackBar(SnackBar(content: Text(text), backgroundColor: error ? Colors.red.shade700 : null));

/// Runs an API action, showing the backend's own message on failure.
Future<T?> guarded<T>(BuildContext context, Future<T> Function() action, {String? success}) async {
  try {
    final r = await action();
    if (success != null && context.mounted) showMessage(context, success);
    return r;
  } catch (e) {
    if (context.mounted) showMessage(context, errorText(context, e), error: true);
    return null;
  }
}

Future<bool> confirmDialog(BuildContext context, String message, {String? confirmLabel, bool danger = false}) async =>
    await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        content: Text(message),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: Text(c.l.cancel)),
          FilledButton(
            key: const Key('confirm'),
            style: danger ? FilledButton.styleFrom(backgroundColor: Colors.red.shade700) : null,
            onPressed: () => Navigator.pop(c, true),
            child: Text(confirmLabel ?? c.l.confirm),
          ),
        ],
      ),
    ) ??
    false;

String money(Object? v) => v == null ? '—' : Money.parse(v.toString()).format();

String shortDate(String? iso) {
  if (iso == null) return '—';
  final d = DateTime.tryParse(iso);
  if (d == null) return iso;
  final k = d.toUtc().add(const Duration(hours: 3)); // Africa/Kampala
  String two(int x) => x.toString().padLeft(2, '0');
  return '${k.year}-${two(k.month)}-${two(k.day)} ${two(k.hour)}:${two(k.minute)}';
}

/// Loading / error-with-retry / data for an async value.
class AsyncBody<T> extends StatelessWidget {
  const AsyncBody({super.key, required this.value, required this.data, this.onRetry});
  final AsyncSnapshotLike<T> value;
  final Widget Function(T) data;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    if (value.error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.cloud_off, size: 48),
            const SizedBox(height: 8),
            Text(errorText(context, value.error!), textAlign: TextAlign.center),
            if (onRetry != null) TextButton(onPressed: onRetry, child: Text(context.l.retry)),
          ]),
        ),
      );
    }
    if (value.data == null) return const Center(child: CircularProgressIndicator());
    return data(value.data as T);
  }
}

class AsyncSnapshotLike<T> {
  const AsyncSnapshotLike(this.data, this.error);
  final T? data;
  final Object? error;
}

/// FutureBuilder with loading / error+retry states.
class Loader<T> extends StatefulWidget {
  const Loader({super.key, required this.load, required this.builder});
  final Future<T> Function() load;
  final Widget Function(BuildContext, T, VoidCallback reload) builder;
  @override
  State<Loader<T>> createState() => _LoaderState<T>();
}

class _LoaderState<T> extends State<Loader<T>> {
  late Future<T> _f = widget.load();
  void _reload() => setState(() => _f = widget.load());
  @override
  Widget build(BuildContext context) => FutureBuilder<T>(
        future: _f,
        builder: (c, s) => AsyncBody<T>(
          value: AsyncSnapshotLike<T>(s.hasData ? s.data : null, s.error),
          onRetry: _reload,
          data: (d) => RefreshIndicator(onRefresh: () async => _reload(), child: widget.builder(c, d, _reload)),
        ),
      );
}
