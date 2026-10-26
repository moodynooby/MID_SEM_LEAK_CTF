# APK Reverse Engineer: Suspect's Companion App
## Case File: The Mid-Sem Leak — IEEE AUSB CTF 2026

**Track:** Binary & Crypto / Mobile Reverse Engineering  
**Difficulty:** Medium (500 pts dynamic: 500 initial / 15 decay / 100 min)  
**Author:** Vidit (@viditd1-eng)  
**Target File:** `files/GICT_Companion.apk`  
**Flag:** `case{apk_decompiled_jadx_secret_extracted}`  

---

### 1. Narrative & Canon Lore
In Act IV of the investigation, forensics responders cataloged physical artifacts recovered from the crime scene at GICT Lab 207. Beside the unlocked Linux workstation, investigators recovered an Android smartphone belonging to TA Piyush Pelaiya. 

A sideloaded application named **GICT Companion** (`org.ieee.ausb.gictcompanion`) was active in background processes. Piyush used this custom build to maintain an unauthorized persistent API session into Prof. Chelaiya's grading portal. The app includes an internal authentication and handshake controller (`SecurityVerification`) that reconstructs the master vault authorization token.

---

### 2. Anti-AI Defensive Layer
- **No Plaintext Strings:** Textbook CTF APKs place flags in `strings.xml` or hardcode plaintext strings in Java classes, which can be scraped instantly with `strings` or LLMs reading raw dumps.
- **Dynamic XOR Key Schedule:** In `GICT_Companion.apk`, the secret is stored as a byte array (`ENC_PAYLOAD`) and decrypted using a multi-term dynamic schedule involving the loop index, a linear transformation, and a periodic key:
  $$\text{decrypted}[i] = \text{ENC\_PAYLOAD}[i] \oplus ((0\text{x}5A \cdot (i + 1) + 0\text{x}42) \pmod{256}) \oplus \text{AUTH\_SALT}[i \pmod{|\text{AUTH\_SALT}|}]$$
- Automated prompt-injection or passive LLM scrapers without runtime symbolic evaluation cannot deduce the key without reverse-calculating the mathematical transformations.

---

### 3. Step-by-Step Walkthrough Solution

#### Step 1: Inspect the APK with JADX-GUI
Open `GICT_Companion.apk` in [JADX](https://github.com/skylot/jadx) or run CLI decompiler:
```bash
jadx -d decompiled_apk files/GICT_Companion.apk
```

#### Step 2: Analyze `MainActivity.java`
Navigate to `org.ieee.ausb.gictcompanion.MainActivity`:
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
Inspect `org.ieee.ausb.gictcompanion.SecurityVerification`:
```java
public final class SecurityVerification {
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
    -72, -34, 96, -101, 32, 13, -8, 75, 5, -3, 4, 76, -17, 11, -89, -64,
    21, -86, -53, 84, -101, -52, 126, -115, 26, 86, -15, 38, 52, -101, 110,
    -21, -26, 15, -79, -52, 109, -94, -57, 114, -111, 36
]
auth_salt = b"GICT_2026_AUTH_KEY_AUSB"
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
