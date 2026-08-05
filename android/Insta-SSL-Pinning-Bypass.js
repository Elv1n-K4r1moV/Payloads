//Tested on Instagram v395 to v430
//Try this code out now by running --> $ frida --codeshare ferozomer/instagram-ssl-pinning-bypass -f YOUR_BINARY

Java.perform(function() {
    console.log("--- Session Guard Disabled ---");
    console.log("--- Patching identity check logic ---");

    var IdentityGate = Java.use("com.facebook.mobilenetwork.internal.certificateverifier.CertificateVerifier");

    IdentityGate.verify.overload(
        '[Ljava.security.cert.X509Certificate;',
        'java.lang.String',
        'boolean'
    ).implementation = function(chain, endpoint, trustFlag) {
        console.log("[*] Identity check bypassed for endpoint: " + endpoint);
        console.log("[*] Returning early. Host is now trusted.");
        return;
    };

    console.log("[*] Patch on identity verification routine is active.");
});
