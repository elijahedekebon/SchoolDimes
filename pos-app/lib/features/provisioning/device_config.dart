import 'dart:convert';

/// What a provisioned device knows about itself (from GET /pos/device/).
class DeviceConfig {
  DeviceConfig({required this.baseUrl, required this.token, required this.info, required this.adminPinHash});

  final String baseUrl;
  final String token;
  final Map<String, dynamic> info;
  final String adminPinHash;

  int get deviceId => info['id'] as int;
  String get deviceName => info['device_name'] as String;
  String get role => info['device_role'] as String; // canteen | merchant | attendance
  bool get canSell => info['can_sell'] == true;
  bool get canRecordAttendance => info['can_record_attendance'] == true;
  bool get canP2p => info['can_p2p'] == true;
  Map<String, dynamic> get school => (info['school'] as Map).cast<String, dynamic>();
  String get schoolName => school['name'] as String;
  String get defaultLanguage => (school['default_language'] as String?) ?? 'en';
  Map<String, dynamic>? get merchant => (info['merchant'] as Map?)?.cast<String, dynamic>();
  int? get merchantId => merchant?['id'] as int?;
  Map<String, dynamic> get settings => (info['settings'] as Map).cast<String, dynamic>();
  int get pinLockoutThreshold => (settings['pin_lockout_threshold'] as num?)?.toInt() ?? 5;

  Map<String, dynamic> toJson() => {'base_url': baseUrl, 'token': token, 'info': info, 'admin_pin_hash': adminPinHash};

  static DeviceConfig fromJson(Map<String, dynamic> j) => DeviceConfig(
        baseUrl: j['base_url'] as String,
        token: j['token'] as String,
        info: (j['info'] as Map).cast<String, dynamic>(),
        adminPinHash: j['admin_pin_hash'] as String,
      );

  DeviceConfig copyWith({Map<String, dynamic>? info, String? token, String? baseUrl, String? adminPinHash}) => DeviceConfig(
      baseUrl: baseUrl ?? this.baseUrl,
      token: token ?? this.token,
      info: info ?? this.info,
      adminPinHash: adminPinHash ?? this.adminPinHash);

  String encode() => jsonEncode(toJson());
}

/// The dashboard's provisioning QR (docs/API_CONTRACTS.md, Section E):
/// {"type":"schooldimes_device","v":1,"api_base_url":"http://…:8000","device_token":"…"}
class ProvisioningCode {
  ProvisioningCode(this.apiBaseUrl, this.deviceToken);
  final String apiBaseUrl;
  final String deviceToken;

  /// Returns null for anything that isn't a SchoolDimes device code.
  static ProvisioningCode? parse(String raw) {
    try {
      final j = jsonDecode(raw.trim());
      if (j is! Map || j['type'] != 'schooldimes_device' || j['v'] != 1) return null;
      final url = j['api_base_url'], token = j['device_token'];
      if (url is! String || token is! String || token.length < 20) return null;
      final uri = Uri.tryParse(url);
      if (uri == null || !(uri.scheme == 'http' || uri.scheme == 'https') || uri.host.isEmpty) return null;
      return ProvisioningCode(url.replaceAll(RegExp(r'/+$'), ''), token);
    } on FormatException {
      return null;
    }
  }
}
