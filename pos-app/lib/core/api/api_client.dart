import 'dart:io';

import 'package:dio/dio.dart';

import '../config/env.dart';

/// Every failure the backend (or the network) can give us, in one shape.
class ApiException implements Exception {
  ApiException({this.statusCode, this.code, this.detail, this.body, this.network = false, this.timeout = false});

  final int? statusCode;
  final String? code;
  final String? detail;
  final Object? body;

  /// No response at all (offline, DNS, refused connection).
  final bool network;

  /// The request may or may not have reached the server.
  final bool timeout;

  /// "Invalid or revoked device token." -> stop transacting, re-provision.
  bool get revoked => statusCode == 401;

  /// The server never got it, or we can't tell: keep the record queued.
  bool get unreachable => network || timeout || (statusCode != null && statusCode! >= 500);

  List<String> get violations =>
      body is Map && (body as Map)['violations'] is List ? List<String>.from((body as Map)['violations'] as List) : const [];

  @override
  String toString() => 'ApiException($statusCode, $code, $detail${network ? ', network' : ''}${timeout ? ', timeout' : ''})';
}

/// The device endpoints the app uses (ApiClient in the app, fakes in tests).
abstract interface class PosApi {
  Future<Map<String, dynamic>> device();
  Future<Map<String, dynamic>> cache({String? since});
  Future<Map<String, dynamic>> roster({String? since});
  Future<Map<String, dynamic>> sync(List<Map<String, dynamic>> transactions, List<Map<String, dynamic>> pinFailures);
  Future<Map<String, dynamic>> purchase(Map<String, dynamic> sale);
  Future<Map<String, dynamic>> p2pTransfer(Map<String, dynamic> body);
  Future<Map<String, dynamic>> attendanceTaps(List<Map<String, dynamic>> taps);
}

/// Device-token client for the documented /api/v1/ device endpoints.
/// Never sends a user JWT.
class ApiClient implements PosApi {
  ApiClient({required String baseUrl, required this.token, String? language, Dio? dio})
      : _dio = dio ??
            Dio(BaseOptions(
              baseUrl: '${baseUrl.replaceAll(RegExp(r'/+$'), '')}/api/v1',
              connectTimeout: const Duration(seconds: 6),
              sendTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 20),
              responseType: ResponseType.json,
            )) {
    _dio.options.headers.addAll({
      'Authorization': 'Device $token',
      'X-App-Version': Env.appVersion,
      'Accept-Language': ?language,
    });
  }

  final Dio _dio;
  final String token;

  set language(String lang) => _dio.options.headers['Accept-Language'] = lang;

  Future<Map<String, dynamic>> _call(Future<Response<dynamic>> Function() send) async {
    try {
      final r = await send();
      return (r.data as Map).cast<String, dynamic>();
    } on DioException catch (e) {
      final res = e.response;
      if (res != null) {
        final body = res.data;
        final map = body is Map ? body : const {};
        throw ApiException(
          statusCode: res.statusCode,
          code: map['code']?.toString() ?? map['reason']?.toString(),
          detail: map['detail']?.toString(),
          body: body,
        );
      }
      final timeout = e.type == DioExceptionType.receiveTimeout || e.type == DioExceptionType.sendTimeout;
      final network = !timeout &&
          (e.type == DioExceptionType.connectionError ||
              e.type == DioExceptionType.connectionTimeout ||
              e.error is SocketException);
      throw ApiException(network: network || !timeout, timeout: timeout, detail: e.message);
    }
  }

  @override
  Future<Map<String, dynamic>> device() => _call(() => _dio.get('/pos/device/'));

  @override
  Future<Map<String, dynamic>> cache({String? since}) =>
      _call(() => _dio.get('/pos/cache/', queryParameters: {'since': ?since}));

  @override
  Future<Map<String, dynamic>> roster({String? since}) =>
      _call(() => _dio.get('/attendance/roster/', queryParameters: {'since': ?since}));

  @override
  Future<Map<String, dynamic>> sync(List<Map<String, dynamic>> transactions, List<Map<String, dynamic>> pinFailures) =>
      _call(() => _dio.post('/pos/sync/', data: {'transactions': transactions, 'pin_failures': pinFailures}));

  /// Online sale. Short timeout: on a timeout the caller queues the sale
  /// offline with the SAME idempotency key (it can never be charged twice).
  @override
  Future<Map<String, dynamic>> purchase(Map<String, dynamic> sale) => _call(() => _dio.post('/pos/purchase/',
      data: sale, options: Options(receiveTimeout: Env.onlineTimeout, sendTimeout: Env.onlineTimeout)));

  @override
  Future<Map<String, dynamic>> p2pTransfer(Map<String, dynamic> body) => _call(() => _dio.post('/pos/p2p-transfer/',
      data: body, options: Options(receiveTimeout: Env.onlineTimeout, sendTimeout: Env.onlineTimeout)));

  @override
  Future<Map<String, dynamic>> attendanceTaps(List<Map<String, dynamic>> taps) =>
      _call(() => _dio.post('/attendance/tap/', data: {'taps': taps}));
}
