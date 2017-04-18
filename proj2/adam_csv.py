#!/bin/env python3.6
# -*- coding: utf-8 -*-

import argparse
import _csv as csv
import sys
import re
import copy
from xml.sax.saxutils import escape

# print message to stderr & exit with return num
def cerr(errmsg, result):
    print(errmsg, file=sys.stderr)
    sys.exit(result)

# open input CSV file
def open_csv_in(filename):
    csvfile = None
    try:
        csvfile = open(filename, newline='', encoding='utf-8')
    except:
        cerr("Cannot open input file'{}'!".format(filename), 2)

    return csvfile

# open output CSV file
def open_xml_out(filename):
    xmlfile = None
    try:
        xmlfile = open(filename, mode='w', newline='', encoding='utf-8')
    except:
        cerr("Cannot open output file'{}'!".format(filename), 2)

    return xmlfile

# get utf-8 string
def to_utf8(s):
    return s.encode().decode("utf-8")

# check if element name is valid
def is_element_name(el_name):
    # regular expression according to xml standard
    name_start_char = \
    ":|[A-Z]|_|[a-z]|[\xC0-\xD6]|[\xD8-\xF6]|" \
    "[\xF8-\u02FF]|[\u0370-\u037D]|[\u037F-\u1FFF]|" \
    "[\u200C-\u200D]|[\u2070-\u218F]|[\u2C00-\u2FEF]|" \
    "[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]|[\U00010000-\U000EFFFF]"

    name_char = name_start_char + "|\-|\.|[0-9]|[\xB7]|[\u0300-\u036F]|[\u203F-\u2040]"
    name = "("+name_start_char+")"+"("+name_char+")*"

    pattern = to_utf8(name) 

    if name and re.fullmatch(pattern, el_name):
        return True 
    return False

# try to correct bad element name, subst = substitution string
def correct_el_name(el_name, subst):
    # regular expression according to xml standard
    name_start_char = \
    ":|[A-Z]|_|[a-z]|[\xC0-\xD6]|[\xD8-\xF6]|" \
    "[\xF8-\u02FF]|[\u0370-\u037D]|[\u037F-\u1FFF]|" \
    "[\u200C-\u200D]|[\u2070-\u218F]|[\u2C00-\u2FEF]|" \
    "[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]|[\U00010000-\U000EFFFF]"

    name_char = "{}|\-|\.|[0-9]|[\xB7]|[\u0300-\u036F]|[\u203F-\u2040]".format(name_start_char)
    name = "({})({})*".format(name_start_char, name_char)

    nsc_pat = to_utf8(name_start_char) 
    nc_pat = to_utf8(name_char) 

    valid_str = ""
    if el_name:
        # is the first char of name valid?
        if not re.fullmatch(nsc_pat, el_name[0]):
            valid_str += subst 
        # the other chars?
        for c in el_name:
            sub = c
            if not re.fullmatch(nc_pat, c):
                sub = subst
            valid_str += sub
        if is_element_name(valid_str): 
            return valid_str
    return None 

def copy_rows(csv):
    rows = []
    for row in csv:
        cells = []
        for cell in row:
           cells.append(cell) 
        rows.append(cells)

    return rows

def init_options():
    argparser = argparse.ArgumentParser(description=\
    "Skript pro konverzi formátu CSV (viz RFC 4180) do XML."\
    "Každému řádku CSV odpovídá jeden dodeﬁnovaný párový element"\
    "a ten bude obsahovat elementy pro jednotlivé sloupce."\
    "Tyto elementy pak již budou obsahovat textovou hodnotu dané buňky z CSV zdroje." 
             , allow_abbrev=False, add_help=False)

    argparser.add_argument("--help", 
                        help="Skript pro konverzi CSV formatu do formatu XML",
                        action="store_true")

    argparser.add_argument("--output",
                        metavar="filename", 
                        help="textový výstupní XML soubor"
                        "s obsahem převedeným ze vstupního souboru.")

    argparser.add_argument("--input",
                        metavar="filename", 
                        help="zadaný vstupní CSV soubor v UTF-8")

    argparser.add_argument("-r",
                        metavar="root-element", 
                        help="jméno párového kořenového elementu obalující výsledek")

    argparser.add_argument("-s", 
                        metavar="separator", 
                        help="nastavení separátoru (jeden znak) "
                        "buněk (resp. sloupců) na každém řádku vstupního CSV")

    argparser.add_argument("-n", 
                        help="negenerovat XML hlavičku na výstup skriptu",
                        action="store_true")

    argparser.add_argument("-c", 
                        default="col",
                        metavar="column-element", 
                        help="určuje preﬁx jména elementu column-elementX, "
                        "který bude obalovat nepojmenované buňky (resp. sloupce)")

    argparser.add_argument("-h", 
                        nargs="?",
                        const="-",
                        metavar="subst", 
                        help="první řádek (přesněji první záznam) "
                        "CSV souboru slouží jako hlavička")

    argparser.add_argument("-i", 
                        help="zajistí vložení atributu index "
                        "s číselnou hodnotou do elementu line-element", action="store_true")

    argparser.add_argument("-l", 
                        metavar="line-element", 
                        help="jméno elementu, který obaluje zvlášť "
                        "každý řádek vstupního CSV")

    argparser.add_argument("--start", 
                        metavar="n", 
                        type=int,
                        help=" inicializace inkrementálního čitače "
                        "pro parametr -i na zadané kladné celé číslo n včetně nuly ")

    argparser.add_argument("--missing-field", 
                        metavar="val", 
                        help="Pokud nějaká vstupní buňka (sloupec) chybí,"
                        "tak je doplněna zde uvedená hodnota val místo pouze prázdného pole")

    argparser.add_argument("--all-columns", 
                        help="Sloupce, které jsou v nekorektním CSV navíc, "
                        "nejsou ignorovány, ale jsou také vloženy do výsledného XML", 
                        action="store_true")

    argparser.add_argument("-e", "--error-recovery", 
                        help="zotavení z chybného počtu sloupců "
                        "na neprvním řádku", action="store_true")

    return argparser

def parse_args():
    # TODO: help argument correct behaviour

    parser = init_options()
    args = None
    try:
        args = parser.parse_args()
    except:
        cerr("Parsovani argumentu chybovalo!", 1)

    if args.help:
        if len(sys.argc) > 2:
            cerr("--help nebylo zadano samostatne!", 1)
        parser.print_help()
        sys.exit(0)

    if args.input == None:
        args.input = sys.stdin
    else:
        args.input = open_csv_in(args.input)

    if args.output == None:
        args.output = sys.stdout
    else:
        args.output = open_xml_out(args.output)

    if args.r:
        if not is_element_name(args.r):
            cerr("nazev root-element nevyhovuje specifikaci!", 30)

    if args.c:
        if not is_element_name(args.c):
            cerr("nazev column-element nevyhovuje specifikaci!", 30)

    if args.l:
        if not is_element_name(args.l):
            cerr("nazev line-element nevyhovuje specifikaci!", 30)

    if args.i and args.l == None:
        cerr("Nespravna kombinace parametru! (-i musi byt zadano s -l)", 1)

    if args.start != None and (not args.l or not args.i):
        cerr("Nespravna kombinace parametru! (--start musi byt zadan s -l a -i)", 1)

    if args.start != None and args.start < 0:
        cerr("--start nesmi byt mensi jak nula!", 1)

    if args.missing_field and not args.error_recovery:
        cerr("Nespravna kombinace parametru! (--missing-field musi byt zadan s -e nebo --error_recovery)", 1)

    if args.all_columns and not args.error_recovery:
        cerr("Nespravna kombinace parametru! (--all-columns musi byt zadan s -e nebo --error_recovery)", 1)

    if not args.s:
        args.s = ","
    if args.s == "TAB":
        args.s = "\t" 
    if not args.l:
        args.l = "row"
    if not args.all_columns:
        args.all_columns = "col"

    return args;


# get parsed csv file
def parse_csv(dlmtr, csvfile):
    csvret = csv.reader(csvfile, delimiter=dlmtr, quotechar='"')
    if not csvret:
        cerr("Chybny format vstupniho souboru!", 4)
    return csvret

# get XML header
def generate_header():
    return '<?xml version="1.0" encoding="UTF-8"?>\n'

# get root element
def generate_root_el(name,end):
    root_tag = "<{}>\n".format(name)

    if end:
        root_tag = "</{}>\n".format(name)

    return root_tag

# control indentation class
class Indent(object):
    """ Simple indentation control """
    def __init__(self, spaces):
        self._cur = ""
        self._tab = spaces

    def tab(self):
        self._cur += self._tab 

    def untab(self):
        self._cur = self._cur[:-len(self._tab)]

    def tabs(self):
        return self._cur

# generate XML string
def create_xml(csv, opts):
    # need mutable copy
    rows = copy_rows(csv)

    # result
    xmlstr = ""

    # unescape entity references
    for row in rows:
        for i in range(len(row)):
            row[i] = escape(row[i])

    # generate XML header if '-n' is not set
    if not opts.n:
        xmlstr += generate_header()

    # XML indentation (default 4 spaces)
    tab = Indent("    ")
    
    # write root element if '-r' is set
    if opts.r:
        xmlstr += generate_root_el(opts.r, end=False)
        tab.tab()

    # first row is header 
    header = None 
    if opts.h:
        if rows:
            header = copy.deepcopy(rows[0])
            for i in range(len(header)):
                valid_str = correct_el_name(header[i], opts.h)
                if valid_str: 
                    header[i] = valid_str
                else:
                    cerr("-h nastaveno, ale nazev elementu '{}'"\
                         "zustal nevalidni!".format(valid_str), 31)
            del rows[0]

    # column counter
    X = 1

    # index of row
    start = 1
    if opts.start:
        start = opts.start

    # first row columns count
    clmn_cnt = None
    if opts.error_recovery and rows:
        clmn_cnt = len(rows[0])
        if opts.h:
            clmn_cnt = len(header)

        # traverse all rows
        for i in range(len(rows)):
            row_len = len(rows[i])
            if row_len > clmn_cnt:
                if not opts.all_columns:
                    # shrink to fit column count
                    shrink = rows[i]
                    rows[i] = shrink[:clmn_cnt]
            elif row_len < clmn_cnt:
                for j in range(clmn_cnt-row_len,row_len):
                    if opts.missing_field:
                        rows[i].append(opts.missing_field)
                    else:
                        rows[i].append("")

    row0_len = 0
    if rows:
        row0_len = len(rows[0])

    for row in rows:
        if not opts.error_recovery and row0_len != len(row):
            cerr("Pocet sloupcu na radku neodpovida poctu sloupcu na prvnim radku!", 32)

        if opts.i:
            xmlstr += '{}<{} index="{}">\n'.format(tab.tabs(), opts.l, str(start))
        else:
            xmlstr += '{}<{}>\n'.format(tab.tabs(), opts.l)

        X = 1
        i = 0

        tab.tab()
        for cell in row:
            hdr_len = -1
            if header:
                hdr_len = len(header)

            if opts.h and i < hdr_len:
                xmlstr += '{}<{}>\n'.format(tab.tabs(), header[i])
                tab.tab()
            elif opts.all_columns or not opts.h:
                xmlstr += '{}<{}{}>\n'.format(tab.tabs(), opts.c, X)
                tab.tab()

            # print column value
            if cell and (opts.h and i < hdr_len) or opts.all_columns or not opts.h:
                xmlstr += '{}{}\n'.format(tab.tabs(), cell)

            if opts.h and i < hdr_len:
                tab.untab()
                xmlstr += '{}</{}>\n'.format(tab.tabs(), header[i])
            elif opts.all_columns or not opts.h:
                tab.untab()
                xmlstr += '{}</{}{}>\n'.format(tab.tabs(), opts.c, X)

            i += 1
            X += 1

        tab.untab()
        start += 1
        xmlstr += '{}</{}>\n'.format(tab.tabs(), opts.l)

    # root element end tag
    if opts.r:
        xmlstr += generate_root_el(opts.r, end=True)

    return xmlstr

if __name__ == '__main__':
    # program options
    options = parse_args()

    # parse input file, opts.s = separator 
    csv = parse_csv(options.s, options.input)
    xml = create_xml(csv, options)

    # write out xml
    if options.output:
        options.output.write(xml)

    sys.exit(0)
