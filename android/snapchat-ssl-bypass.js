// 
//

// uee  example : frida -U  --codeshare mr-blackhole/snapchat-ssl-bypass-all-new-version-of-2026 -f com.snapchat.android

// Try this code out now by running ---> $ frida --codeshare mr-blackhole/snapchat-ssl-bypass-all-new-version-of-2026 -f YOUR_BINARY

const moduleName = "libclient.so";
const pattern = "fd 7b ba a9 fc 6f 01 a9 fd 03 00 91 fa 67 02 a9 f8 5f 03 a9 f6 57 04 a9 f4 4f 05 a9 ff 03 0e d1 53 d0 3b d5";

// Wait for module to load
function waitForModule(name, callback) {
    const m = Process.findModuleByName(name);
    if (m) return callback(m);
    setTimeout(() => waitForModule(name, callback), 100);
}

// Native function hook
function hookNative(lib, pattern) {
    const ranges = Process.enumerateRanges('r--')
        .filter(r => r.base.compare(lib.base) >= 0 && r.base.add(r.size).compare(lib.base.add(lib.size)) <= 0);

    ranges.forEach(r => {
        try {
            Memory.scan(r.base, r.size, pattern, {
                onMatch(addr) {
                    console.log("[*] Hooking function at:", addr);
                    Interceptor.attach(addr, {
                        onEnter(args) {
                            console.log("[*] Function called!", "arg0:", args[0], "arg1:", args[1], "arg2:", args[2]);
                        },
                        onLeave(retval) {
                            console.log("[*] Original return:", retval.toInt32());
                            retval.replace(1); // force success
                            console.log("[*] Replaced return:", retval.toInt32());
                        }
                    });
                    return 'stop';
                }
            });
        } catch (e) {
            console.log("[!] Memory scan exception:", e.message);
        }
    });
}

// Java SSL bypass
Java.perform(() => {
    const Log = Java.use("android.util.Log");
    const logger = msg => {
        console.log(msg);
        Log.v("SNAPCHAT_SSL_BYPASS", msg);
    }

    try {
        const SSLContext = Java.use("javax.net.ssl.SSLContext");
        const X509TrustManager = Java.use("javax.net.ssl.X509TrustManager");

        const TrustManager = Java.registerClass({
            implements: [X509TrustManager],
            methods: {
                checkClientTrusted(chain, authType) {},
                checkServerTrusted(chain, authType) {},
                getAcceptedIssuers() {
                    return [];
                }
            },
            name: "com.leftenter.snapchat.CustomTrustManager"
        });

        SSLContext.init.overload(
            "[Ljavax.net.ssl.KeyManager;",
            "[Ljavax.net.ssl.TrustManager;",
            "java.security.SecureRandom"
        ).implementation = function(km, tmOld, sr) {
            logger("[*] SSLContext.init hooked, using custom TrustManager");
            return this.init(km, [TrustManager.$new()], sr);
        };
        logger("[*] Java SSL hooks installed");
    } catch (e) {
        logger("[!] Failed Java SSL hook: " + e);
    }

    try {
        const TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        if (TrustManagerImpl.checkTrustedRecursive) {
            const ArrayList = Java.use("java.util.ArrayList");
            TrustManagerImpl.checkTrustedRecursive.implementation = function() {
                logger("[*] checkTrustedRecursive called - returning empty ArrayList");
                return ArrayList.$new();
            }
        }
    } catch (e) {
        logger("[!] checkTrustedRecursive hook failed: " + e);
    }
});

// Wait for module then hook native
waitForModule(moduleName, lib => {
    console.log("[*] Module loaded:", JSON.stringify(lib));
    hookNative(lib, pattern);
});
