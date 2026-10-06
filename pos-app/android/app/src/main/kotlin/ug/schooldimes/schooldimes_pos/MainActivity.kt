package ug.schooldimes.schooldimes_pos

import io.flutter.embedding.android.FlutterFragmentActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.util.concurrent.Executors
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.PBEKeySpec

/**
 * FlutterFragmentActivity (needed by local_auth) plus one method channel:
 * PBKDF2-HMAC-SHA256 from the platform's crypto provider, so verifying a
 * Django PIN hash (870,000 iterations) stays fast on low-end terminals.
 * The PIN is only held in memory for the derivation and never logged.
 */
class MainActivity : FlutterFragmentActivity() {
    private val worker = Executors.newSingleThreadExecutor()

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "ug.schooldimes.pos/pbkdf2")
            .setMethodCallHandler { call, result ->
                if (call.method != "derive") {
                    result.notImplemented()
                    return@setMethodCallHandler
                }
                val password = call.argument<String>("password") ?: ""
                val salt = call.argument<String>("salt") ?: ""
                val iterations = call.argument<Int>("iterations") ?: 0
                val bits = call.argument<Int>("keyLengthBits") ?: 256
                worker.execute {
                    try {
                        val chars = password.toCharArray()
                        // Java's PBEKeySpec takes a char[]; for ASCII PINs this equals UTF-8 bytes.
                        val spec = PBEKeySpec(chars, salt.toByteArray(Charsets.UTF_8), iterations, bits)
                        val key = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).encoded
                        spec.clearPassword()
                        java.util.Arrays.fill(chars, '\u0000')
                        runOnUiThread { result.success(key) }
                    } catch (e: Exception) {
                        runOnUiThread { result.error("pbkdf2_failed", e.javaClass.simpleName, null) }
                    }
                }
            }
    }
}
