#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
CLC bio assembly file CAS, and the tabular format generated by `assembly_table
-n -s -p`
"""

import sys

from itertools import groupby
from optparse import OptionParser

from jcvi.formats.base import LineFile
from jcvi.formats.blast import report_pairs
from jcvi.apps.grid import GridProcess
from jcvi.apps.base import ActionDispatcher, debug
from jcvi.utils.range import range_distance
debug()


class CasTabLine (LineFile):
    """
    The table generate by command `assembly_table -n -s -p` 
    from clcbio assembly cell
    """
    def __init__(self, line):
        args = line.split()
        self.readnum = args[0] # usually integer or `-`
        self.readname = args[1]
        self.readlen = int(args[-10])
        # 0-based indexing
        self.readstart = int(args[-9])
        if self.readstart >=0: self.readstart += 1
        
        self.readstop = int(args[-8])
        self.refnum = int(args[-7])
        
        self.refstart = int(args[-6])
        if self.refstart >=0: self.refstart += 1

        self.refstop = int(args[-5])

        self.is_reversed = (int(args[-4])==1)
        self.strand = '-' if self.is_reversed else '+'

        self.nummatches = int(args[-3])
        self.is_paired = (int(args[-2])==1)
        self.score = int(args[-1])

    def __str__(self):
        return "\t".join(str(x) for x in (self.readname, self.refnum, 
            self.refstart-1, self.refstop, self.score, self.orientation))


def main():
    
    actions = (
        ('split', 'split the CAS file into smaller CAS using sub_assembly'),
        ('bed', 'convert cas tabular output to bed format'),
        ('pairs', 'print paired-end reads of cas tabular output'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def split(args):
    """
    %prog split casfile 1 10

    split the binary casfile by using CLCbio `sub_assembly` program, the two
    numbers are starting and ending index for the `reference`; useful to split
    one big assembly per contig
    """
    p = OptionParser(split.__doc__)
    opts, args = p.parse_args(args)

    if len(args) != 3:
        sys.exit(p.print_help())

    casfile, start, end = args
    start = int(start)
    end = int(end)

    split_cmd = "sub_assembly -a {casfile} -o sa.{i}.cas -s {i} " + \
        "-e sa.{i}.pairs.fasta -f sa.{i}.fragments.fasta -g sa.{i}.ref.fasta"

    for i in range(start, end+1):
        cmd = split_cmd.format(casfile=casfile, i=i)
        p = GridProcess(cmd)
        p.start(path=None) # current dir


def bed(args):
    """
    %prog bed cas_tabbed

    convert the format into bed format
    """
    
    p = OptionParser(bed.__doc__)
    opts, args = p.parse_args(args)

    if len(args)!=1:
        sys.exit(p.print_help())

    castabfile = args[0]
    fp = open(castabfile)
    for row in fp:
        b = CasTabLine(row)
        if b.readstart!=-1:
            print b


def pairs(args):
    """
    %prog pairs cas_tabbed
    
    report summary of the cas tabular results, how many paired ends mapped, avg
    distance between paired ends, etc
    """
    p = OptionParser(pairs.__doc__)
    p.add_option("--cutoff", dest="cutoff", default=1e9, type="int",
            help="distance to call valid links between PE [default: %default]")
    p.add_option("--pairs", dest="pairsfile", 
            default=False, action="store_true",
            help="write valid pairs to pairsfile")
    p.add_option("--inserts", dest="insertsfile", default=True, 
            help="write insert sizes to insertsfile and plot distribution " + \
            "to insertsfile.pdf")
    opts, args = p.parse_args(args)

    if len(args)!=1:
        sys.exit(p.print_help())

    cutoff = opts.cutoff
    if cutoff < 0: cutoff = 1e9
    castabfile = args[0]

    basename = castabfile.split(".")[0]
    pairsfile = ".".join((basename, "pairs")) if opts.pairsfile else None
    insertsfile = ".".join((basename, "inserts")) if opts.insertsfile else None

    fp = open(castabfile)
    data = [CasTabLine(row) for row in fp]
    data.sort(key=lambda x: x.readname)

    report_pairs(data, cutoff, dialect="cas", pairsfile=pairsfile,
           insertsfile=insertsfile)


if __name__ == '__main__':
    main()
