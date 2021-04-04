#!/usr/bin/env python3
#
# Extract content of OALD9 dictionary file (oup_en-dic.lld).
# Copyright (c) 2018, Hiroyuki Ohsaki.
# All rights reserved.
#
# $Id: extract.py,v 1.4 2019/05/27 07:10:20 ohsaki Exp ohsaki $
#

# exapmle: extract.py oup_en-dic.lld >oup_en-dic.txt

import mmap
import re
import struct
import sys

ENTRY_START_MARKER = b"\x90\x38\x45\x39"

TRANS_TBL = {
    0x20: ' ',
    0x21: '.',
    0x22: '-',
    0x23: ',',
    0x25: '>',
}

TRANS_3E_TBL = {
    0x01: ':',
    0x02: ';',
    0x03: '+',
    0x05: '/',
    0x06: '=',
    0x08: "'",
    0x09: "\"",
    0x14: '!',
    0x15: '?',
    0x16: '#',
    0x17: '$',
    0x18: '%',
    0x19: '&',
    0x1b: '(',
    0x1c: ')',
    0x1f: '[',
    0x20: ']',
    0x23: '#',
    0x26: '-',
    0x2b: '*',
}

TRANS_3B_TBL = {
    0x08: '`',
    0x09: "'",
    0x23: "・",
    0x2b: "x",
}

def get_6bit_char(buf):
    # convert to binary string
    binstr = ''
    for c in buf:
        binstr += f'{c:08b}'

    # chop six bits from left
    pos = 0
    while pos < len(binstr):
        c = int(binstr[pos:pos + 6], 2)
        yield c
        pos += 6
        if c == 0x00:
            # advance to the next byte boundary
            while pos % 8 != 0:
                pos += 1
            # skip (possibly) binary-encoded part
            if buf[pos // 8:pos // 8 + 2] == b'\x10\x04':
                pos += 8 * 3

def decode(buf):
    astr = ''
    g = get_6bit_char(buf)
    try:
        while True:
            c = next(g)
            if 0x01 <= c <= 0x1a:  # a-z
                s = chr(0x60 + c)
            elif c == 0x24:
                c = next(g)
                c = next(g)
                s = '<'
            elif c in TRANS_TBL:
                s = TRANS_TBL[c]
            elif c == 0x3b:
                c = next(g)
                if c in TRANS_3B_TBL:
                    s = TRANS_3B_TBL[c]
                else:
                    s = f'[3b{c:02x}]'
            elif c == 0x3e:
                c = next(g)
                if 0x0a <= c <= 0x13:
                    s = chr(0x30 + (c - 0x0a))
                elif c in TRANS_3E_TBL:
                    s = TRANS_3E_TBL[c]
                else:
                    s = f'[3e{c:02x}]'
            elif c == 0x3d:  # A-Z
                c = next(g)
                s = chr(0x41 + c - 0x20)
            elif c == 0x3f:
                c1 = next(g)
                c2 = next(g)
                c3 = next(g)
                c4 = next(g)
                s = f'#{c1:02x}{c2:02x}{c3:02x}{c4:02x}'
            elif c == 0x00:
                s = '<br/>'
            else:
                s = f' {c:02x} '
            astr += s
    except StopIteration:
        return astr

def main():
    with open(sys.argv[1], 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
    offset = struct.unpack('<I', mm[0xa8:0xa8 + 4])[0]
    for buf in mm[offset:].split(ENTRY_START_MARKER):
        if buf:
            astr = decode(ENTRY_START_MARKER + buf)
            astr = re.sub('(</entry>).*', r'\1', astr)
            print(astr)

if __name__ == "__main__":
    main()
