import 'dart:async';
import 'dart:io';

import 'package:dio/dio.dart';

import '../config/env.dart';
import '../storage/token_store.dart';

/// Same error shape as the POS app's ApiException.
class ApiException implements Exception {
  ApiException({this.statusCode, this.code, this.detail, this.body, this.network = false});

  final int? statusCode;
  final String? code;
  final String? detail;
  final Object? body;
  final bool network;

  bool get unauthorized => statusCode == 401;

  /// Field errors from DRF ({"field": ["msg"]}).
  Map<String, List<String>> get fieldErrors {
    if (body is! Map) return const {};
    final out = <String, List<String>>{};
    (body as Map).forEach((k, v) {
      if (k is String && v is List && k != 'violations') out[k] = v.map((e) => e.toString()).toList();
    });
    return out;
  }

  /// The backend's own (already translated) message.
  String get message {
    if (detail != null) return detail!;
    final f = fieldErrors;
    if (f.isNotEmpty) return f.entries.map((e) => e.key == 'non_field_errors' ? e.value.join(' ') : '${e.key}: ${e.value.join(' ')}').join('\n');
    return code ?? (network ? 'network' : 'HTTP $statusCode');
  }

  @override
  String toString() => 'ApiException($statusCode, $code, $detail)';
}

/// JWT client for /api/v1/. Adds the Bearer token, refreshes ONCE on a 401
/// (one in-flight refresh shared by concurrent requests, because refresh
/// tokens rotate and are blacklisted on use) and retries the request.
class ApiClient {
  ApiClient({required this.tokens, String? baseUrl, Dio? dio, this.onSignedOut})
      : _dio = dio ?? Dio(BaseOptions(
              baseUrl: '${(baseUrl ?? Env.apiBaseUrl).replaceAll(RegExp(r'/+$'), '')}/api/v1',
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 25),
            )) {
    _dio.interceptors.add(QueuedInterceptorsWrapper(
      onRequest: (o, h) async {
        final access = await tokens.access();
        if (access != null && o.extra['auth'] != false) o.headers['Authorization'] = 'Bearer $access';
        if (language != null) o.headers['Accept-Language'] = language;
        h.next(o);
      },
      onError: (e, h) async {
        final req = e.requestOptions;
        if (e.response?.statusCode == 401 && req.extra['auth'] != false && req.extra['retried'] != true) {
          final ok = await _refresh();
          if (ok) {
            req.extra['retried'] = true;
            req.headers['Authorization'] = 'Bearer ${await tokens.access()}';
            try {
              return h.resolve(await _dio.fetch(req));
            } on DioException catch (e2) {
              return h.next(e2);
            }
          }
          await tokens.clear();
          onSignedOut?.call();
        }
        h.next(e);
      },
    ));
  }

  final Dio _dio;
  final TokenStore tokens;
  void Function()? onSignedOut;
  String? language;
  Future<bool>? _refreshing;

  Future<bool> _refresh() => _refreshing ??= () async {
        try {
          final refresh = await tokens.refresh();
          if (refresh == null) return false;
          final r = await _dio.post('/auth/refresh', data: {'refresh': refresh}, options: Options(extra: {'auth': false}));
          await tokens.save(r.data['access'] as String, r.data['refresh'] as String);
          return true;
        } catch (_) {
          return false;
        } finally {
          scheduleMicrotask(() => _refreshing = null);
        }
      }();

  Future<T> _call<T>(Future<Response<dynamic>> Function() send) async {
    try {
      final r = await send();
      return r.data as T;
    } on DioException catch (e) {
      final res = e.response;
      if (res != null) {
        final b = res.data;
        final map = b is Map ? b : const {};
        throw ApiException(statusCode: res.statusCode, code: map['code']?.toString(), detail: map['detail']?.toString(), body: b);
      }
      throw ApiException(network: true, detail: e.error is SocketException ? null : e.message);
    }
  }

  Future<dynamic> get(String path, {Map<String, dynamic>? query, bool auth = true}) =>
      _call(() => _dio.get(path, queryParameters: query, options: Options(extra: {'auth': auth})));
  Future<dynamic> post(String path, [Object? body, bool auth = true]) =>
      _call(() => _dio.post(path, data: body ?? {}, options: Options(extra: {'auth': auth})));
  Future<dynamic> patch(String path, Object body) => _call(() => _dio.patch(path, data: body));
  Future<dynamic> put(String path, Object body) => _call(() => _dio.put(path, data: body));
  Future<dynamic> delete(String path) => _call(() => _dio.delete(path));

  /// Raw text (CSV export).
  Future<String> getText(String path, {Map<String, dynamic>? query}) =>
      _call(() => _dio.get(path, queryParameters: query, options: Options(responseType: ResponseType.plain)));
}
