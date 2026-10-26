#!/usr/bin/env python3
"""
Challenge Artifact Generator: Suspect's Companion App
Track: Binary & Crypto / Mobile Reversing
Case File: The Mid-Sem Leak (IEEE AUSB CTF 2026)

Compiles and packages GICT_Companion.apk containing obfuscated authentication
and dynamic XOR token reconstruction logic.
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent
DIST_DIR = CHALLENGE_DIR / "files"
OUTPUT_APK = DIST_DIR / "GICT_Companion.apk"

MANIFEST_XML = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="org.ieee.ausb.gictcompanion"
    android:versionCode="1"
    android:versionName="1.0.4-dev">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <application
        android:allowBackup="false"
        android:icon="@android:drawable/sym_def_app_icon"
        android:label="GICT Companion"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.Material.Light.NoActionBar">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

MAIN_ACTIVITY_JAVA = """package org.ieee.ausb.gictcompanion;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

public class MainActivity extends Activity {
    private EditText inputToken;
    private TextView textStatus;
    private Button btnVerify;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Simple programmatic UI to avoid resource compile dependencies
        android.widget.LinearLayout layout = new android.widget.LinearLayout(this);
        layout.setOrientation(android.widget.LinearLayout.VERTICAL);
        layout.setPadding(32, 32, 32, 32);

        TextView header = new TextView(this);
        header.setText("GICT Lab 207/208 Companion [Debug v1.0.4]");
        header.setTextSize(18);
        layout.addView(header);

        TextView subHeader = new TextView(this);
        subHeader.setText("Property of TA Piyush Pelaiya - Department of CS&E");
        subHeader.setTextSize(12);
        layout.addView(subHeader);

        inputToken = new EditText(this);
        inputToken.setHint("Enter Faculty Auth Token / API Session Key");
        layout.addView(inputToken);

        btnVerify = new Button(this);
        btnVerify.setText("Validate Handshake Session");
        layout.addView(btnVerify);

        textStatus = new TextView(this);
        textStatus.setText("Status: Awaiting handshake validation...");
        layout.addView(textStatus);

        btnVerify.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String token = inputToken.getText().toString();
                if (SecurityVerification.verifyHandshakeToken(token)) {
                    textStatus.setText("ACCESS GRANTED: " + SecurityVerification.getMasterKey());
                } else {
                    textStatus.setText("ERROR: Invalid Auth Token. Check faculty session logs.");
                }
            }
        });

        setContentView(layout);
    }
}
"""

SECURITY_VERIFICATION_JAVA = """package org.ieee.ausb.gictcompanion;

/**
 * Confidential Security Verification Layer
 * Author: TA Piyush Pelaiya (GICT CS&E)
 * Notice: Do not distribute outside Lab 207 private network.
 */
public final class SecurityVerification {
    // Dynamic obfuscated payload synthesized from dynamic XOR key schedule
    // Target flag: case{apk_decompiled_jadx_secret_extracted}
    private static final byte[] ENC_PAYLOAD = new byte[] {
        (byte) -72, (byte) -34, (byte) 96, (byte) -101, (byte) 32, (byte) 13, (byte) -8, (byte) 75,
        (byte) 5, (byte) -3, (byte) 4, (byte) 76, (byte) -17, (byte) 11, (byte) -89, (byte) -64,
        (byte) 21, (byte) -86, (byte) -53, (byte) 84, (byte) -101, (byte) -52, (byte) 126, (byte) -115,
        (byte) 26, (byte) 86, (byte) -15, (byte) 38, (byte) 52, (byte) -101, (byte) 110, (byte) -21,
        (byte) -26, (byte) 15, (byte) -79, (byte) -52, (byte) 109, (byte) -94, (byte) -57, (byte) 114,
        (byte) -111, (byte) 36
    };

    private static final byte[] AUTH_SALT = "GICT_2026_AUTH_KEY_AUSB".getBytes();
    private static final int SCHEDULE_SALT = 0x5a;

    private SecurityVerification() {}

    /**
     * Handshake integrity check performed on incoming authentication token.
     */
    public static boolean verifyHandshakeToken(String candidate) {
        if (candidate == null || candidate.length() != 16) {
            return false;
        }
        // Hash check: SHA-256 of candidate must match expected session token hash
        try {
            java.security.MessageDigest md = java.security.MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(candidate.getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) {
                sb.append(String.format("%02x", b));
            }
            // "chelaiya_oop99!" -> SHA-256 prefix check
            return sb.toString().startsWith("4c2e5b9");
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Synthesizes master vault authorization token from dynamic XOR key schedule.
     */
    public static String getMasterKey() {
        byte[] result = new byte[ENC_PAYLOAD.length];
        for (int i = 0; i < ENC_PAYLOAD.length; i++) {
            int k = AUTH_SALT[i % AUTH_SALT.length] & 0xff;
            int mask = (SCHEDULE_SALT * (i + 1) + 0x42) & 0xff;
            int b = ENC_PAYLOAD[i] & 0xff;
            result[i] = (byte) (b ^ mask ^ k);
        }
        try {
            return new String(result, "UTF-8");
        } catch (Exception e) {
            return "";
        }
    }
}
"""

def find_android_tools():
    possible_roots = [
        os.environ.get("ANDROID_HOME", ""),
        os.environ.get("ANDROID_SDK_ROOT", ""),
        str(Path.home() / "Android" / "Sdk"),
        "/usr/lib/android-sdk",
    ]
    sdk_root = None
    for r in possible_roots:
        if r and os.path.isdir(r):
            sdk_root = Path(r)
            break

    if not sdk_root:
        raise RuntimeError("Android SDK root not found. Please set ANDROID_HOME.")

    # Find build tools
    build_tools_dir = sdk_root / "build-tools"
    if not build_tools_dir.exists():
        raise RuntimeError("No build-tools directory found in Android SDK.")
    
    versions = sorted(build_tools_dir.glob("*"), reverse=True)
    if not versions:
        raise RuntimeError("No build-tools versions found.")
    bt_dir = versions[0]

    # Find android.jar
    platforms_dir = sdk_root / "platforms"
    platforms = sorted(platforms_dir.glob("android-*"), reverse=True)
    if not platforms:
        raise RuntimeError("No platforms found in Android SDK.")
    android_jar = platforms[0] / "android.jar"

    tools = {
        "d8": bt_dir / "d8",
        "aapt2": bt_dir / "aapt2",
        "zipalign": bt_dir / "zipalign",
        "apksigner": bt_dir / "apksigner",
        "android_jar": android_jar,
        "javac": shutil.which("javac"),
        "keytool": shutil.which("keytool"),
    }
    return tools

def build_apk():
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    tools = find_android_tools()
    print(f"[*] Using Android tools from: {tools['d8'].parent}")
    print(f"[*] Using android.jar: {tools['android_jar']}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src_dir = tmp_path / "src" / "org" / "ieee" / "ausb" / "gictcompanion"
        src_dir.mkdir(parents=True, exist_ok=True)

        manifest_file = tmp_path / "AndroidManifest.xml"
        manifest_file.write_text(MANIFEST_XML)

        main_activity_file = src_dir / "MainActivity.java"
        main_activity_file.write_text(MAIN_ACTIVITY_JAVA)

        security_file = src_dir / "SecurityVerification.java"
        security_file.write_text(SECURITY_VERIFICATION_JAVA)

        classes_dir = tmp_path / "classes"
        classes_dir.mkdir(parents=True, exist_ok=True)

        print("[*] Compiling Java classes with javac...")
        cmd_javac = [
            str(tools["javac"]),
            "-source", "17",
            "-target", "17",
            "-cp", str(tools["android_jar"]),
            "-d", str(classes_dir),
            str(main_activity_file),
            str(security_file),
        ]
        subprocess.run(cmd_javac, check=True)

        print("[*] Translating bytecode to Dalvik DEX via d8...")
        dex_dir = tmp_path / "dex"
        dex_dir.mkdir(parents=True, exist_ok=True)
        class_files = [str(p) for p in classes_dir.rglob("*.class")]
        cmd_d8 = [
            str(tools["d8"]),
            "--lib", str(tools["android_jar"]),
            "--output", str(dex_dir),
        ] + class_files
        subprocess.run(cmd_d8, check=True)

        print("[*] Packaging APK with aapt2 link...")
        unaligned_apk = tmp_path / "unaligned.apk"
        cmd_aapt = [
            str(tools["aapt2"]),
            "link",
            "-I", str(tools["android_jar"]),
            "--manifest", str(manifest_file),
            "-o", str(unaligned_apk),
        ]
        subprocess.run(cmd_aapt, check=True)

        # Add classes.dex into unaligned.apk
        classes_dex = dex_dir / "classes.dex"
        cmd_zip = ["zip", "-j", str(unaligned_apk), str(classes_dex)]
        subprocess.run(cmd_zip, check=True, cwd=str(tmp_path))

        print("[*] Aligning APK via zipalign...")
        aligned_apk = tmp_path / "aligned.apk"
        cmd_align = [
            str(tools["zipalign"]),
            "-p", "-f", "4",
            str(unaligned_apk),
            str(aligned_apk),
        ]
        subprocess.run(cmd_align, check=True)

        print("[*] Signing APK with debug keystore...")
        keystore_file = tmp_path / "debug.keystore"
        cmd_keytool = [
            str(tools["keytool"]),
            "-genkeypair",
            "-keystore", str(keystore_file),
            "-storepass", "android",
            "-keypass", "android",
            "-alias", "androiddebugkey",
            "-dname", "CN=Android Debug,O=Android,C=US",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
        ]
        subprocess.run(cmd_keytool, check=True)

        cmd_sign = [
            str(tools["apksigner"]),
            "sign",
            "--ks", str(keystore_file),
            "--ks-pass", "pass:android",
            "--key-pass", "pass:android",
            "--out", str(OUTPUT_APK),
            str(aligned_apk),
        ]
        subprocess.run(cmd_sign, check=True)

    print(f"[+] Successfully generated: {OUTPUT_APK}")
    print(f"[+] File size: {OUTPUT_APK.stat().st_size} bytes")

if __name__ == "__main__":
    build_apk()
