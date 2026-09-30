/*
 * JOCKY Spectre Agent — Linux Collector
 * Enumerates processes via /proc, network via /proc/net,
 * files via directory traversal with stat() time filtering.
 *
 * Compiled with: gcc -O2 -static collector.c -o collector -lcrypto
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <openssl/sha.h>

#define MAX_EVIDENCE 4096

typedef struct {
    char    id[16];
    int     artifact_type;
    char    sha256[65];
    char    path[256];
    time_t  timestamp;
} evidence_item_t;

typedef struct {
    evidence_item_t items[MAX_EVIDENCE];
    int             count;
} collection_result_t;

static void sha256_file(const char *path, char *out) {
    FILE *f = fopen(path, "rb");
    if (!f) { out[0] = '\0'; return; }

    SHA256_CTX ctx;
    SHA256_Init(&ctx);

    unsigned char buf[8192];
    size_t n;
    while ((n = fread(buf, 1, sizeof(buf), f)) > 0)
        SHA256_Update(&ctx, buf, n);
    fclose(f);

    unsigned char hash[32];
    SHA256_Final(hash, &ctx);
    for (int i = 0; i < 32; i++)
        sprintf(out + i*2, "%02x", hash[i]);
}

/* Enumerate processes from /proc */
static int collect_processes(collection_result_t *result) {
    DIR *proc = opendir("/proc");
    if (!proc) return 0;

    int count = 0;
    struct dirent *entry;
    while ((entry = readdir(proc)) != NULL) {
        /* PID directories are numeric */
        char *end;
        long pid = strtol(entry->d_name, &end, 10);
        if (*end != '\0' || pid <= 0) continue;

        char cmdline_path[64];
        snprintf(cmdline_path, sizeof(cmdline_path), "/proc/%ld/cmdline", pid);

        FILE *f = fopen(cmdline_path, "r");
        if (!f) continue;

        char cmdline[256] = {0};
        fread(cmdline, 1, sizeof(cmdline)-1, f);
        fclose(f);

        if (result->count < MAX_EVIDENCE) {
            evidence_item_t *item = &result->items[result->count];
            snprintf(item->id, sizeof(item->id), "E-%05d", result->count + 1);
            item->artifact_type = 1;  /* PROCESS */
            snprintf(item->path, sizeof(item->path), "/proc/%ld", pid);
            item->timestamp = time(NULL);
            result->count++;
            count++;
        }
    }
    closedir(proc);
    return count;
}

/* Enumerate network connections from /proc/net/tcp and /proc/net/udp */
static int collect_network(collection_result_t *result) {
    const char *net_files[] = { "/proc/net/tcp", "/proc/net/tcp6",
                                "/proc/net/udp", "/proc/net/udp6" };
    int count = 0;

    for (int i = 0; i < 4; i++) {
        FILE *f = fopen(net_files[i], "r");
        if (!f) continue;

        char line[512];
        fgets(line, sizeof(line), f);  /* Skip header */

        while (fgets(line, sizeof(line), f)) {
            if (result->count < MAX_EVIDENCE) {
                evidence_item_t *item = &result->items[result->count];
                snprintf(item->id, sizeof(item->id), "E-%05d", result->count + 1);
                item->artifact_type = 3;  /* NETWORK */
                strncpy(item->path, net_files[i], sizeof(item->path)-1);
                item->timestamp = time(NULL);
                result->count++;
                count++;
            }
        }
        fclose(f);
    }
    return count;
}

/* Enumerate files in target directories with modification time filter */
static int collect_files(collection_result_t *result,
                         const char **paths, int path_count,
                         int modified_within_hours) {
    int count = 0;
    time_t cutoff = time(NULL) - (modified_within_hours * 3600);

    for (int i = 0; i < path_count; i++) {
        DIR *dir = opendir(paths[i]);
        if (!dir) continue;

        struct dirent *entry;
        while ((entry = readdir(dir)) != NULL) {
            if (entry->d_name[0] == '.') continue;

            char fullpath[512];
            snprintf(fullpath, sizeof(fullpath), "%s/%s", paths[i], entry->d_name);

            struct stat st;
            if (stat(fullpath, &st) != 0) continue;
            if (!S_ISREG(st.st_mode)) continue;
            if (st.st_mtime < cutoff) continue;

            if (result->count < MAX_EVIDENCE) {
                evidence_item_t *item = &result->items[result->count];
                snprintf(item->id, sizeof(item->id), "E-%05d", result->count + 1);
                item->artifact_type = 2;  /* FILE */
                strncpy(item->path, fullpath, sizeof(item->path)-1);
                sha256_file(fullpath, item->sha256);
                item->timestamp = time(NULL);
                result->count++;
                count++;
            }
        }
        closedir(dir);
    }
    return count;
}

int main(int argc, char *argv[]) {
    collection_result_t result = {0};

    int procs   = collect_processes(&result);
    int network = collect_network(&result);

    const char *search_paths[] = { "/tmp", "/var/tmp" };
    int files = collect_files(&result, search_paths, 2, 72);

    fprintf(stderr, "Collection complete: %d processes, %d network, %d files\n",
            procs, network, files);

    /* Serialize evidence to stdout as JSON for beacon transport */
    printf("{\"total\": %d, \"items\": [", result.count);
    for (int i = 0; i < result.count; i++) {
        if (i > 0) printf(",");
        printf("{\"id\":\"%s\",\"type\":%d,\"path\":\"%s\"}",
               result.items[i].id, result.items[i].artifact_type,
               result.items[i].path);
    }
    printf("]}\n");

    return 0;
}
