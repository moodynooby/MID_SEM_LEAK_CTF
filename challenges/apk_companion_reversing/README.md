# APK Reverse Engineer: Suspect's Companion App
## Case File: The Mid-Sem Leak — IEEE AUSB CTF 2026

**Track:** Binary & Crypto / Mobile Reverse Engineering  
**Difficulty:** Medium — 500 → 200 pts (decay 16 solves)  
**Author:** Vidit (@viditd1-eng)  
**Target File:** `files/AU_Companion.apk`  
**Flag:** `case{apk_decompiled_jadx_secret_extracted}`  

---

### 1. Narrative & Canon Lore
In Act IV of the investigation, forensics responders cataloged physical artifacts recovered from the crime scene at AU Lab 207. Beside the unlocked Linux workstation, investigators recovered an Android smartphone belonging to TA Piyush Pelaiya. 

A sideloaded application named **AU Companion** (`org.ieee.ausb.aucompanion`) was active in background processes. Piyush used this custom build to maintain an unauthorized persistent API session into Prof. Chelaiya's grading portal. The app includes an internal authentication and handshake controller (`SecurityVerification`) that reconstructs the master vault authorization token.

---

### 2. Anti-AI Defensive Layer
- **No Plaintext Strings:** Textbook CTF APKs place flags in `strings.xml` or hardcode plaintext strings in Java classes, which can be scraped instantly with `strings` or LLMs reading raw dumps.
- **Dynamic XOR Key Schedule:** In `AU_Companion.apk`, the secret is stored as a byte array (`ENC_PAYLOAD`) and decrypted using a multi-term dynamic schedule involving the loop index, a linear transformation, and a periodic key:
  $$\text{decrypted}[i] = \text{ENC\_PAYLOAD}[i] \oplus ((0\text{x}5A \cdot (i + 1) + 0\text{x}42) \pmod{256}) \oplus \text{AUTH\_SALT}[i \pmod{|\text{AUTH\_SALT}|}]$$
- Automated prompt-injection or passive LLM scrapers without runtime symbolic evaluation cannot deduce the key without reverse-calculating the mathematical transformations.

---

### 3. Step-by-Step Walkthrough Solution

#### Step 1: Inspect the APK with JADX-GUI
Open `AU_Companion.apk` in [JADX](https://github.com/skylot/jadx) or run CLI decompiler:
```bash
jadx -d decompiled_apk files/AU_Companion.apk
```

#### Step 2: Analyze `MainActivity.java`
Navigate to `org.ieee.ausb.aucompanion.MainActivity`:
```java
btnVerify.setOnClickListener(new View.OnClickListener() {
    @Override
    public void onClick(View v) {
        String token = inputToken.getText().toString();
        if (SecurityVerification.verifyHandshakeToken(token)) {
            textStatus.setText("ACCESS GRANTED: " + SecurityVerification.getMasterKey());
        }
    }
});
```
Notice that when validation succeeds, `SecurityVerification.getMasterKey()` is invoked to obtain the master authorization key.

#### Step 3: Analyze `SecurityVerification.java`
Inspect `org.ieee.ausb.aucompanion.SecurityVerification`:
```java
public final class SecurityVerification {
    private static final byte[] ENC_PAYLOAD = new byte[] {
        (byte) -66, (byte) -62, (byte) 124, (byte) -3, (byte) 79, (byte) 13, (byte) -2, (byte) 38,
        (byte) 114, (byte) -9, (byte) 17, (byte) 81, (byte) -28, (byte) 8, (byte) -67, (byte) -46,
        (byte) 15, (byte) -78, (byte) -63, (byte) 70, (byte) -116, (byte) -34, (byte) 105, (byte) -107,
        (byte) 97, (byte) 37, (byte) -105, (byte) 79, (byte) 89, (byte) -22, (byte) 9, (byte) -119,
        (byte) -15, (byte) 17, (byte) -81, (byte) -35, (byte) 124, (byte) -94, (byte) -51, (byte) 98,
        (byte) -101, (byte) 57
    };

    private static final byte[] AUTH_SALT = "AU_2026_AUTH_KEY_AUSB".getBytes();
    private static final int SCHEDULE_SALT = 0x5a;

    public static String getMasterKey() {
        byte[] result = new byte[ENC_PAYLOAD.length];
        for (int i = 0; i < ENC_PAYLOAD.length; i++) {
            int k = AUTH_SALT[i % AUTH_SALT.length] & 0xff;
            int mask = (SCHEDULE_SALT * (i + 1) + 0x42) & 0xff;
            int b = ENC_PAYLOAD[i] & 0xff;
            result[i] = (byte) (b ^ mask ^ k);
        }
        return new String(result, "UTF-8");
    }
}
```

#### Step 4: Reconstruct the Flag in Python
Replicate the decryption loop in a quick Python solver:
```python
enc_payload = [
    -66, -62, 124, -3, 79, 13, -2, 38, 114, -9, 17, 81, -28, 8, -67, -46,
    15, -78, -63, 70, -116, -34, 105, -107, 97, 37, -105, 79, 89, -22, 9,
    -119, -15, 17, -81, -35, 124, -94, -51, 98, -101, 57
]
auth_salt = b"AU_2026_AUTH_KEY_AUSB"
schedule_salt = 0x5a

flag = ""
for i, b in enumerate(enc_payload):
    k = auth_salt[i % len(auth_salt)]
    mask = (schedule_salt * (i + 1) + 0x42) & 0xff
    flag += chr((b & 0xff) ^ mask ^ k)

print(flag)
```
Output:
```
case{apk_decompiled_jadx_secret_extracted}
```

---

### 4. Automated Solver Verification
Execute the automated test harness:
```bash
python3 solve.py
```
Exit code `0` confirms valid dynamic key decryption.
