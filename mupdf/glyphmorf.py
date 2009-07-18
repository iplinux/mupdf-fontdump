#!/usr/bin/python

import sys

LOOKUP = """

#include "fitz.h"
#include "mupdf.h"

int pdf_lookupagl(char *name, int *ucsbuf, int ucscap)
{
    char buf[256];
    int ucslen = 0;
    char *p;
    char *s;
    int i;

    strlcpy(buf, name, sizeof buf);

    /* kill anything after first period */
    p = strchr(buf, '.');
    if (p)
        p[0] = 0;

    /* split into components separated by underscore */
    p = buf;
    s = strsep(&p, "_");
    while (s)
    {
        int l = 0;
        int r = nelem(aglidx) - 1;

        while (l <= r)
        {
            int m = (l + r) >> 1;
            int c = strcmp(s, aglidx[m].name);
            if (c < 0)
                r = m - 1;
            else if (c > 0)
                l = m + 1;
            else
            {
                for (i = 0; i < aglidx[m].num; i++)
                    ucsbuf[ucslen++] = agldat[aglidx[m].ofs + i];
                goto next;
            }
        }

        if (strstr(s, "uni") == s)
        {
            char tmp[5];
            s += 3;
            while (s[0])
            {
                strlcpy(tmp, s, 5);
                ucsbuf[ucslen++] = strtol(tmp, nil, 16);
                s += MIN(strlen(s), 4);
            }
        }

        else if (strstr(s, "u") == s)
            ucsbuf[ucslen++] = strtol(s + 1, nil, 16);

next:
        s = strsep(&p, "_");
    }

    return ucslen;
}

"""

TEST = """
int main(int argc, char **argv)
{
    int buf[256];
    int len;
    int i, k;

    for (i = 1; i < argc; i++)
    {
        len = pdf_lookupagl(argv[i], buf, nelem(buf));
        printf("'%s' [%d] = ", argv[i], len);
        for (k = 0; k < len; k++)
            printf("%04X ", buf[k]);
        printf("\\n");
    }
}
"""
agl = []
comments = []

f = open("glyphlist.txt", "r")
for line in f.readlines():
	if line[0] == '#':
		comments.append(line.strip());
		continue
	line = line[:-1]
	name, list = line.split(';')
	list = map(lambda x: int(x, 16), list.split(' '))
	agl.append((name, list))

aglidx = []
agldat = []

for name, ucslist in agl:
	num = len(ucslist)
	ofs = len(agldat)
	for ucs in ucslist:
		agldat.append(ucs)
	aglidx.append((name, num, ofs))

print "/* Adobe Glyph List -- autogenerated so do not touch */"

print "/*"
for line in comments:
	print line[:-1];
print "*/"
print

print "static const struct { char *name; short num; short ofs; }",
print "aglidx[%d] = {" % len(aglidx)

for name, num, ofs in aglidx:
	print "{\"%s\",%d,%d}," % (name, num, ofs)

print "};"
print 

print "static const unsigned short agldat[%d] = {" % len(agldat)
c = 0
for ucs in agldat:
	bufd = "%d," % ucs
	bufh = "0x%x," % ucs

	if len(bufd) < len(bufh):
		buf = bufd
	else:
		buf = bufh

	c += len(buf)
	if c > 78:
		c = len(buf)
		print
	sys.stdout.write(buf)

print
print "};"

print LOOKUP
# print TEST

print >>sys.stderr, "idx %d * %d = %d" % (len(aglidx), 8, len(aglidx)*8)
print >>sys.stderr, "dat %d * %d = %d" % (len(agldat), 2, len(agldat)*2)

