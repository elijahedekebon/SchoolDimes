import 'dart:async';
import 'dart:io';

import 'package:nfc_manager/nfc_manager.dart';
import 'package:nfc_manager/nfc_manager_android.dart';
import 'package:nfc_manager/nfc_manager_ios.dart';

import 'uid.dart';

enum NfcState { enabled, disabled, unsupported }

/// Keeps one NFC reader session open while a sale/attendance screen is
/// visible and emits normalised card UIDs. The same card held on the reader
/// is reported once per [repeatAfter].
class NfcReader {
  NfcReader({this.repeatAfter = const Duration(milliseconds: 1500)});

  final Duration repeatAfter;
  final _uids = StreamController<String>.broadcast();
  final _unsupportedTags = StreamController<void>.broadcast();
  bool _running = false;
  String? _lastUid;
  DateTime _lastAt = DateTime.fromMillisecondsSinceEpoch(0);

  Stream<String> get uids => _uids.stream;

  /// Tags with no readable UID (e.g. some phone-emulated cards).
  Stream<void> get unsupportedTags => _unsupportedTags.stream;

  Future<NfcState> state() async {
    try {
      return switch (await NfcManager.instance.checkAvailability()) {
        NfcAvailability.enabled => NfcState.enabled,
        NfcAvailability.disabled => NfcState.disabled,
        NfcAvailability.unsupported => NfcState.unsupported,
      };
    } catch (_) {
      return NfcState.unsupported; // emulator / no plugin
    }
  }

  Future<NfcState> start() async {
    final s = await state();
    if (s != NfcState.enabled || _running) return s;
    _running = true;
    await NfcManager.instance.startSession(
      pollingOptions: {NfcPollingOption.iso14443, NfcPollingOption.iso15693},
      noPlatformSoundsAndroid: false,
      invalidateAfterFirstReadIos: false,
      onDiscovered: (tag) {
        final bytes = Platform.isAndroid ? NfcTagAndroid.from(tag)?.id : (MiFareIos.from(tag)?.identifier ?? Iso7816Ios.from(tag)?.identifier);
        if (bytes == null || bytes.length < 4) {
          _unsupportedTags.add(null);
          return;
        }
        emit(uidFromBytes(bytes));
      },
    );
    return s;
  }

  /// Also used by the dev-only "simulate tap".
  void emit(String uid) {
    final now = DateTime.now();
    if (uid == _lastUid && now.difference(_lastAt) < repeatAfter) return;
    _lastUid = uid;
    _lastAt = now;
    _uids.add(uid);
  }

  Future<void> stop() async {
    if (!_running) return;
    _running = false;
    try {
      await NfcManager.instance.stopSession();
    } catch (_) {}
  }
}
