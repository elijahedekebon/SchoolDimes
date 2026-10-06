import 'dart:typed_data';

/// The backend's canonical card_uid (docs/API_CONTRACTS.md, "Card UID
/// format"): lowercase hex, two digits per byte, in the order the reader
/// returns the bytes (Android Tag.getId()), no separators, 4-32 bytes.
String uidFromBytes(Uint8List bytes) => bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();

/// Normalises typed input ("04:A2:2B:7C", "04 a2 2b 7c", "04-A2…") the same
/// way as cards.services.normalize_card_uid. Returns null if invalid.
String? normalizeUid(String raw) {
  final uid = raw.trim().replaceAll(RegExp(r'[\s:\-]'), '').toLowerCase();
  if (!RegExp(r'^[0-9a-f]{8,64}$').hasMatch(uid) || uid.length.isOdd) return null;
  return uid;
}
