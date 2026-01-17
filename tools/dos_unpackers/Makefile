CC = gcc
CFLAGS = -Wall -O2

all: unlzexe unexepack depklite

unlzexe: unlzexe.c
	$(CC) $(CFLAGS) unlzexe.c -o unlzexe

unexepack: unpack.c
	$(CC) $(CFLAGS) unpack.c -o unexepack

depklite: depklite.c depklite.h
	$(CC) $(CFLAGS) depklite.c -o depklite

clean:
	rm -f unlzexe unexepack depklite

.PHONY: all clean