/// Money as integer cents (UGX has 2 decimal places in the API). Parsed from
/// and printed to the backend's decimal strings ("5000.00"); never a double.
class Money implements Comparable<Money> {
  const Money(this.cents);
  const Money.zero() : cents = 0;

  final int cents;

  static final RegExp _re = RegExp(r'^(-)?(\d+)(?:\.(\d{1,2}))?$');

  /// Parses "5000", "5000.5", "5000.50", "-12.00". Throws on anything else.
  factory Money.parse(String value) {
    final m = _re.firstMatch(value.trim());
    if (m == null) throw FormatException('Not a money amount: "$value"');
    final whole = int.parse(m.group(2)!);
    final frac = int.parse((m.group(3) ?? '').padRight(2, '0'));
    final c = whole * 100 + frac;
    return Money(m.group(1) != null ? -c : c);
  }

  static Money? tryParse(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    try {
      return Money.parse(value);
    } on FormatException {
      return null;
    }
  }

  /// Nullable API field ("null" caps mean "no limit").
  static Money? fromApi(Object? value) => value == null ? null : Money.parse(value.toString());

  Money operator +(Money o) => Money(cents + o.cents);
  Money operator -(Money o) => Money(cents - o.cents);
  Money operator *(int qty) => Money(cents * qty);
  Money operator -() => Money(-cents);
  bool operator <(Money o) => cents < o.cents;
  bool operator <=(Money o) => cents <= o.cents;
  bool operator >(Money o) => cents > o.cents;
  bool operator >=(Money o) => cents >= o.cents;
  bool get isZero => cents == 0;
  bool get isNegative => cents < 0;
  bool get isPositive => cents > 0;

  static Money sum(Iterable<Money> values) => values.fold(const Money.zero(), (a, b) => a + b);

  /// The API's wire format: "5000.00".
  String toApi() {
    final neg = cents < 0;
    final a = cents.abs();
    return '${neg ? '-' : ''}${a ~/ 100}.${(a % 100).toString().padLeft(2, '0')}';
  }

  /// "UGX 15,000" / "UGX 1,500.50".
  String format({bool currency = true}) {
    final neg = cents < 0;
    final a = cents.abs();
    final whole = (a ~/ 100).toString().replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => ',');
    final frac = a % 100;
    final body = frac == 0 ? whole : '$whole.${frac.toString().padLeft(2, '0')}';
    return '${neg ? '-' : ''}${currency ? 'UGX ' : ''}$body';
  }

  @override
  int compareTo(Money other) => cents.compareTo(other.cents);

  @override
  bool operator ==(Object other) => other is Money && other.cents == cents;

  @override
  int get hashCode => cents.hashCode;

  @override
  String toString() => toApi();
}
