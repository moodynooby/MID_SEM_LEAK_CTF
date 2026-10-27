/*
 * SEB_KioskGuard.exe — CTF Challenge Binary
 * Build: x86_64-w64-mingw32-gcc -O2 -s -o SEB_KioskGuard.exe seb_guard.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>
#include <windows.h>
#include <tlhelp32.h>

/* ---------- S-Box (AES S-Box) ---------- */
static const uint8_t SBOX[256] = {
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16
};

/* ---------- Base key (16 bytes) ---------- */
static const uint8_t K_BASE[16] = {
    0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE,
    0x13, 0x37, 0x42, 0x00, 0xF0, 0x0D, 0xC0, 0xDE
};

#define FLAG_LEN 44

/*
 * Ciphertext placeholder — generate.py binary-patches these bytes.
 * Using 0xBB as sentinel (unlikely to collide with real .rdata content).
 */
static const uint8_t CIPHERTEXT[FLAG_LEN] = {
    0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,
    0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,
    0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,
    0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,
    0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,0xBB,
    0xBB,0xBB,0xBB,0xBB
};

/*
 * Expected .text hash — volatile forces the compiler to load from memory,
 * keeping the value in .rdata instead of inlining it as a CMP immediate
 * in .text (which would change the hash on patch).
 */
static volatile const uint32_t EXPECTED_TEXT_HASH = 0xDEADBEEF;

/* ===================== Anti-Debug: PEB Inspection ===================== */
static int check_debugger(void) {
    uint64_t peb = 0;
    __asm__ volatile ("movq %%gs:0x60, %0" : "=r"(peb));

    if (peb) {
        unsigned char beingDebugged = *((unsigned char *)(peb + 0x02));
        if (beingDebugged) return 1;

        uint32_t ntGlobalFlag = *((uint32_t *)(peb + 0xBC));
        if (ntGlobalFlag & 0x70) return 1;
    }

    if (IsDebuggerPresent()) return 1;
    return 0;
}

static int check_remote_debugger(void) {
    BOOL isRemote = FALSE;
    CheckRemoteDebuggerPresent(GetCurrentProcess(), &isRemote);
    return isRemote ? 1 : 0;
}

/* =================== Anti-Debug: Hardware Breakpoints ================= */
static int check_hardware_breakpoints(void) {
    CONTEXT ctx;
    memset(&ctx, 0, sizeof(ctx));
    ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;
    if (GetThreadContext(GetCurrentThread(), &ctx)) {
        if (ctx.Dr0 || ctx.Dr1 || ctx.Dr2 || ctx.Dr3)
            return 1;
    }
    return 0;
}

/* =================== Anti-Debug: Timing (RDTSC) ====================== */
static int check_timing(void) {
    uint32_t lo1, hi1, lo2, hi2;
    __asm__ volatile ("rdtsc" : "=a"(lo1), "=d"(hi1));

    volatile int x = 0;
    for (volatile int i = 0; i < 100; i++) x += i;

    __asm__ volatile ("rdtsc" : "=a"(lo2), "=d"(hi2));

    uint64_t t1 = ((uint64_t)hi1 << 32) | lo1;
    uint64_t t2 = ((uint64_t)hi2 << 32) | lo2;

    if ((t2 - t1) > 10000000ULL) return 1;
    return 0;
}

/* =================== Process Blacklist Scanner ======================== */
static const char *BLACKLIST[] = {
    "x64dbg.exe", "x32dbg.exe", "ghidra.exe", "ida64.exe", "ida.exe",
    "cheatengine", "wireshark.exe", "procexp.exe", "procexp64.exe",
    "ollydbg.exe", "processhacker.exe", "httpdebugger", NULL
};

static int scan_blacklist(void) {
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE) return 0;

    PROCESSENTRY32 pe;
    pe.dwSize = sizeof(pe);
    if (Process32First(snap, &pe)) {
        do {
            for (int i = 0; BLACKLIST[i]; i++) {
                char lower[MAX_PATH];
                strncpy(lower, pe.szExeFile, MAX_PATH - 1);
                lower[MAX_PATH - 1] = '\0';
                for (char *p = lower; *p; p++) *p = (char)tolower((unsigned char)*p);
                if (strstr(lower, BLACKLIST[i])) {
                    CloseHandle(snap);
                    return 1;
                }
            }
        } while (Process32Next(snap, &pe));
    }
    CloseHandle(snap);
    return 0;
}

/* =================== Fake Crash Dialog ================================ */
static void fake_crash_dialog(const char *reason) {
    char msg[512];
    snprintf(msg, sizeof(msg),
        "Safe Exam Browser - Kiosk Guard\n\n"
        "FATAL ERROR: Integrity violation detected.\n"
        "Reason: %s\n\n"
        "The exam session has been terminated.\n"
        "Please contact your proctor immediately.\n\n"
        "Error Code: 0xSEB%04X",
        reason, (unsigned)(GetTickCount() & 0xFFFF));
    MessageBoxA(NULL, msg, "SEB Kiosk Guard - Fatal Error",
                MB_ICONERROR | MB_OK);
}

/* =================== Self-Integrity: FNV-1a over .text ================ */
static uint32_t compute_text_hash(void) {
    HMODULE base = GetModuleHandleA(NULL);
    if (!base) return 0;

    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)base;
    IMAGE_NT_HEADERS *nt  = (IMAGE_NT_HEADERS *)((uint8_t *)base + dos->e_lfanew);
    IMAGE_SECTION_HEADER *sec = IMAGE_FIRST_SECTION(nt);

    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++, sec++) {
        if (memcmp(sec->Name, ".text", 5) == 0) {
            uint8_t *start = (uint8_t *)base + sec->VirtualAddress;
            uint32_t size  = sec->SizeOfRawData;

            uint32_t h = 0x811c9dc5;
            for (uint32_t j = 0; j < size; j++) {
                h ^= start[j];
                h *= 0x01000193;
            }
            return h;
        }
    }
    return 0;
}

/* =================== Decryption Routine =============================== */
static void decrypt_and_print(uint32_t h_text) {
    char flag[FLAG_LEN + 1];
    for (int i = 0; i < FLAG_LEN; i++) {
        uint8_t step1 = (uint8_t)(CIPHERTEXT[i] - SBOX[(i * 7) % 256]);
        uint8_t step2 = step1 ^ K_BASE[(i + h_text) % 16];
        flag[i] = (char)step2;
    }
    flag[FLAG_LEN] = '\0';

    printf("\n");
    printf("==============================================\n");
    printf("  SEB Kiosk Guard - Integrity Verified\n");
    printf("==============================================\n");
    printf("  Config Key validation PASSED.\n");
    printf("  Browser Exam Key: %s\n", flag);
    printf("==============================================\n\n");
}

/* =================== Main ============================================= */
int main(int argc, char *argv[]) {
    printf("Safe Exam Browser - Kiosk Guard v4.2.1\n");
    printf("Initializing secure exam environment...\n\n");

    if (check_debugger()) {
        fake_crash_dialog("Debugger detected (PEB inspection)");
        return 1;
    }
    if (check_remote_debugger()) {
        fake_crash_dialog("Remote debugger attached");
        return 1;
    }
    if (check_hardware_breakpoints()) {
        fake_crash_dialog("Hardware breakpoints active");
        return 1;
    }
    if (check_timing()) {
        fake_crash_dialog("Execution timing anomaly");
        return 1;
    }
    if (scan_blacklist()) {
        fake_crash_dialog("Unauthorized analysis tool running");
        return 1;
    }

    printf("[+] Environment checks passed.\n");
    printf("[+] Verifying kiosk integrity...\n");

    uint32_t h_text = compute_text_hash();
    if (h_text != EXPECTED_TEXT_HASH) {
        fake_crash_dialog("Binary integrity compromised (checksum mismatch)");
        return 1;
    }

    printf("[+] Integrity verified.\n");
    printf("[+] Decrypting exam configuration...\n");

    decrypt_and_print(h_text);
    return 0;
}
