import 'dart:convert';
import 'dart:typed_data';

/// PBKDF2-HMAC-SHA256 with a 32-byte output (one block), in pure Dart.
///
/// Tuned for Django's 870,000 iterations: the HMAC inner/outer key states
/// are computed once, and each iteration is exactly two SHA-256 block
/// compressions over 32-bit words (no allocations in the loop). Used when
/// the platform's native PBKDF2 isn't available (tests, desktop, iOS).
Uint8List pbkdf2Sha256(List<int> password, List<int> salt, int iterations) {
  var key = password;
  if (key.length > 64) key = _sha256Bytes(key);
  final ipad = Uint8List(64), opad = Uint8List(64);
  for (var i = 0; i < 64; i++) {
    final k = i < key.length ? key[i] : 0;
    ipad[i] = k ^ 0x36;
    opad[i] = k ^ 0x5c;
  }
  final innerState = _initState();
  _compress(innerState, _wordsOf(ipad, 0));
  final outerState = _initState();
  _compress(outerState, _wordsOf(opad, 0));

  // U1 = HMAC(P, salt || INT(1)) -- the only variable-length message.
  final first = <int>[...salt, 0, 0, 0, 1];
  final innerDigest = _finish(Uint32List.fromList(innerState), first, 64);
  final u = _finish(Uint32List.fromList(outerState), _bytesOf(innerDigest), 64);
  final t = Uint32List.fromList(u);

  // Every later message is a 32-byte digest: one padded block each.
  final block = Uint32List(16);
  block[8] = 0x80000000;
  block[15] = (64 + 32) * 8;
  final s = Uint32List(8);
  for (var i = 1; i < iterations; i++) {
    for (var j = 0; j < 8; j++) {
      block[j] = u[j];
      s[j] = innerState[j];
    }
    _compress(s, block);
    for (var j = 0; j < 8; j++) {
      block[j] = s[j];
      s[j] = outerState[j];
    }
    _compress(s, block);
    for (var j = 0; j < 8; j++) {
      u[j] = s[j];
      t[j] ^= s[j];
    }
  }
  return _bytesOf(t);
}

/// Django's `pbkdf2_sha256$<iterations>$<salt>$<b64hash>` check, constant time.
bool verifyDjangoPbkdf2(String pin, String encoded, {Uint8List Function(String pin, String salt, int iterations)? derive}) {
  final parts = encoded.split(r'$');
  if (parts.length != 4 || parts[0] != 'pbkdf2_sha256') return false;
  final iterations = int.tryParse(parts[1]);
  if (iterations == null || iterations < 1) return false;
  final Uint8List expected;
  try {
    expected = base64.decode(parts[3]);
  } on FormatException {
    return false;
  }
  final actual = derive != null ? derive(pin, parts[2], iterations) : pbkdf2Sha256(utf8.encode(pin), utf8.encode(parts[2]), iterations);
  if (actual.length != expected.length) return false;
  var diff = 0;
  for (var i = 0; i < actual.length; i++) {
    diff |= actual[i] ^ expected[i];
  }
  return diff == 0;
}

const List<int> _k = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];
final Uint32List _kw = Uint32List.fromList(_k);
final Uint32List _w = Uint32List(64);

Uint32List _initState() => Uint32List.fromList(
    [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);

int _rotr(int x, int n) => ((x >> n) | (x << (32 - n))) & 0xffffffff;

void _compress(Uint32List h, Uint32List block) {
  final w = _w;
  for (var i = 0; i < 16; i++) {
    w[i] = block[i];
  }
  for (var i = 16; i < 64; i++) {
    final x = w[i - 15], y = w[i - 2];
    final s0 = _rotr(x, 7) ^ _rotr(x, 18) ^ (x >> 3);
    final s1 = _rotr(y, 17) ^ _rotr(y, 19) ^ (y >> 10);
    w[i] = w[i - 16] + s0 + w[i - 7] + s1;
  }
  var a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
  for (var i = 0; i < 64; i++) {
    final s1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25);
    final ch = (e & f) ^ ((~e) & 0xffffffff & g);
    final t1 = (hh + s1 + ch + _kw[i] + w[i]) & 0xffffffff;
    final s0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22);
    final maj = (a & b) ^ (a & c) ^ (b & c);
    final t2 = (s0 + maj) & 0xffffffff;
    hh = g;
    g = f;
    f = e;
    e = (d + t1) & 0xffffffff;
    d = c;
    c = b;
    b = a;
    a = (t1 + t2) & 0xffffffff;
  }
  h[0] += a;
  h[1] += b;
  h[2] += c;
  h[3] += d;
  h[4] += e;
  h[5] += f;
  h[6] += g;
  h[7] += hh;
}

Uint32List _wordsOf(List<int> bytes, int offset) {
  final out = Uint32List(16);
  for (var i = 0; i < 16; i++) {
    final o = offset + i * 4;
    out[i] = (bytes[o] << 24) | (bytes[o + 1] << 16) | (bytes[o + 2] << 8) | bytes[o + 3];
  }
  return out;
}

Uint8List _bytesOf(Uint32List words) {
  final out = Uint8List(words.length * 4);
  for (var i = 0; i < words.length; i++) {
    out[i * 4] = words[i] >> 24;
    out[i * 4 + 1] = (words[i] >> 16) & 0xff;
    out[i * 4 + 2] = (words[i] >> 8) & 0xff;
    out[i * 4 + 3] = words[i] & 0xff;
  }
  return out;
}

/// Finishes a SHA-256 whose first [prefixLen] bytes are already in [state].
Uint32List _finish(Uint32List state, List<int> message, int prefixLen) {
  final total = prefixLen + message.length;
  final padded = <int>[...message, 0x80];
  while ((padded.length + 8) % 64 != 0) {
    padded.add(0);
  }
  final bits = total * 8;
  for (var i = 7; i >= 0; i--) {
    padded.add((bits >> (i * 8)) & 0xff);
  }
  for (var o = 0; o < padded.length; o += 64) {
    _compress(state, _wordsOf(padded, o));
  }
  return state;
}

Uint8List _sha256Bytes(List<int> message) => _bytesOf(_finish(_initState(), message, 0));

/// Plain SHA-256 (exposed for tests against known digests).
Uint8List sha256(List<int> message) => _sha256Bytes(message);
