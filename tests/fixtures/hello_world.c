/*
 * hello_world.c – simple C fixture used by AXE feature-validation tests.
 *
 * Purpose: provide a small, self-contained C source file that AXE agents can
 * read, analyse, and comment on during automated testing of batch mode, collab
 * mode, and the /prep / /llmprep / /buildinfo interactive commands.
 *
 * Build:
 *   gcc -o hello_world hello_world.c
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Structure representing a simple key-value pair. */
typedef struct {
    char key[32];
    int  value;
} Entry;

/* Populate an array of entries. */
static void populate(Entry *entries, int n) {
    int i;
    for (i = 0; i < n; i++) {
        snprintf(entries[i].key, sizeof(entries[i].key), "item_%d", i);
        entries[i].value = i * i;
    }
}

/* Print the entry array to stdout. */
static void print_entries(const Entry *entries, int n) {
    int i;
    for (i = 0; i < n; i++) {
        printf("%s = %d\n", entries[i].key, entries[i].value);
    }
}

int main(void) {
    const int N = 5;
    Entry *entries = (Entry *)malloc(N * sizeof(Entry));
    if (!entries) {
        fprintf(stderr, "malloc failed\n");
        return 1;
    }

    populate(entries, N);
    print_entries(entries, N);

    free(entries);
    return 0;
}
