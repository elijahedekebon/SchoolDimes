/// Africa/Kampala is UTC+3 all year (no daylight saving), so "today" and
/// "this week" for caps and summaries can be computed without a tz database.
abstract final class Kampala {
  static const Duration offset = Duration(hours: 3);

  /// Wall-clock time in Kampala, as a UTC-flagged DateTime holding local fields.
  static DateTime wall(DateTime instant) => instant.toUtc().add(offset);

  /// The Kampala calendar day ("YYYY-MM-DD") of an instant.
  static String day(DateTime instant) => wall(instant).toIso8601String().substring(0, 10);

  /// Monday of the instant's Kampala week ("YYYY-MM-DD").
  static String weekStart(DateTime instant) {
    final w = wall(instant);
    final monday = DateTime.utc(w.year, w.month, w.day).subtract(Duration(days: w.weekday - 1));
    return monday.toIso8601String().substring(0, 10);
  }

  /// ISO-8601 with the +03:00 offset, the form sent as device_local_timestamp.
  static String isoLocal(DateTime instant) {
    final w = wall(instant);
    String two(int v) => v.toString().padLeft(2, '0');
    return '${w.year.toString().padLeft(4, '0')}-${two(w.month)}-${two(w.day)}'
        'T${two(w.hour)}:${two(w.minute)}:${two(w.second)}+03:00';
  }
}
