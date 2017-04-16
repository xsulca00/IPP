#!/bin/env python3.6
# -*- coding: utf-8 -*-

import _csv as csv
import sys
import copy
import argparse
import re

# help message
help_msg= "Skript pro konverzi formátu CSV (viz RFC 4180) do XML. Každému řádku CSV odpovídá jeden dodeﬁnovaný párový element (viz parametr -l) a ten bude obsahovat elementy pro jednotlivé sloupce (viz parametr -h). Tyto elementy pak již budou obsahovat textovou hodnotu dané buňky z CSV zdroje." 

def print_err(*args):
    sys.stderr.write(' '.join(map(str,args)) + '\n')

def open_input(filename):
    # try open input file
    csvfile = None
    if filename == "stdin":
        csvfile = sys.stdin
    else:
        try:
            csvfile = open(filename, newline='', encoding='utf-8')
        except:
            print_err("Cannot open input file'",filename,"'!")
            sys.exit(2)

    return csvfile

def open_output(filename):
    xmlfile = None
    if filename == "stdout":
        xmlfile = sys.stdout
    else:
        try:
            xmlfile = open(filename, mode='w', newline='', encoding='utf-8')
        except:
            print_err("Cannot open output file'",filename,"'!")
            sys.exit(3)
    return xmlfile

# replace - if opts.h is set
def is_element_name(tag, replace, opts):
    # regular expression according to xml standard
    name_start_char = \
    ":|[A-Z]|_|[a-z]|[\xC0-\xD6]|[\xD8-\xF6]|" \
    "[\xF8-\u02FF]|[\u0370-\u037D]|[\u037F-\u1FFF]|" \
    "[\u200C-\u200D]|[\u2070-\u218F]|[\u2C00-\u2FEF]|" \
    "[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]|[\U00010000-\U000EFFFF]"

    name_char = name_start_char + "|\-|\.|[0-9]|[\xB7]|[\u0300-\u036F]|[\u203F-\u2040]"
    name = "("+name_start_char+")"+"("+name_char+")*"

    bytes = name.encode()
    pattern = bytes.decode("utf-8")

    if replace:
        string = ""
        # loop over symbols in string and replace
        if tag:
            bts = name_start_char.encode()
            pat = bts.decode("utf-8")
            if not re.fullmatch(pat, tag[0]):
                string += opts.h
        bts = name_char.encode()
        pat = bts.decode("utf-8")
        for c in tag:
            if not re.fullmatch(pat, c):
                 string += opts.h
            else:
                 string += c
        if re.fullmatch(pattern, string):
            return string
        return ""
    if re.fullmatch(pattern, tag):
        return True 
    return False

def copy_rows(csv):
    rows = []
    for row in csv:
        cells = []
        for cell in row:
           cells.append(cell) 
        rows.append(cells)

    return rows

TAB="    "

def parse_args():
    parser = argparse.ArgumentParser(description=help_msg, allow_abbrev=False, add_help=False)
    # TODO: help argument correct behaviour
    parser.add_argument("--help", 
                        help="Skript pro konverzi CSV formatu do formatu XML",
                        action="store_true")

    parser.add_argument("--input",
                        metavar="filename", 
                        help="zadaný vstupní CSV soubor v UTF-8")

    parser.add_argument("--output",
                        metavar="filename", 
                        help="textový výstupní XML soubor"
                        "s obsahem převedeným ze vstupního souboru.")

    parser.add_argument("-n", 
                        help="negenerovat XML hlavičku na výstup skriptu",
                        action="store_true")

    parser.add_argument("-r",
                        metavar="root-element", 
                        help="jméno párového kořenového elementu obalující výsledek")

    parser.add_argument("-s", 
                        metavar="separator", 
                        help="nastavení separátoru (jeden znak) "
                        "buněk (resp. sloupců) na každém řádku vstupního CSV")

    parser.add_argument("-h", 
                        nargs="?",
                        const="-",
                        metavar="subst", 
                        help="první řádek (přesněji první záznam) "
                        "CSV souboru slouží jako hlavička")

    parser.add_argument("-c", 
                        default="col",
                        metavar="column-element", 
                        help="určuje preﬁx jména elementu column-elementX, "
                        "který bude obalovat nepojmenované buňky (resp. sloupce)")

    parser.add_argument("-l", 
                        metavar="line-element", 
                        help="jméno elementu, který obaluje zvlášť "
                        "každý řádek vstupního CSV")

    parser.add_argument("-i", 
                        help="zajistí vložení atributu index "
                        "s číselnou hodnotou do elementu line-element", action="store_true")

    parser.add_argument("--start", 
                        metavar="n", 
                        type=int,
                        help=" inicializace inkrementálního čitače "
                        "pro parametr -i na zadané kladné celé číslo n včetně nuly ")

    parser.add_argument("-e", "--error-recovery", 
                        help="zotavení z chybného počtu sloupců "
                        "na neprvním řádku", action="store_true")

    parser.add_argument("--missing-field", 
                        metavar="val", 
                        help="Pokud nějaká vstupní buňka (sloupec) chybí,"
                        "tak je doplněna zde uvedená hodnota val místo pouze prázdného pole")

    parser.add_argument("--all-columns", 
                        help="Sloupce, které jsou v nekorektním CSV navíc, "
                        "nejsou ignorovány, ale jsou také vloženy do výsledného XML", 
                        action="store_true")

    args = None
    try:
        args = parser.parse_args()
    except:
        print_err("Chyba behem parsovani!")
        sys.exit(1)

    if args.help:
        if len(sys.argv) > 2:
            print_err("Zadano vice argumentu spolu s --help!")
            sys.exit(1)
        parser.print_help()
        sys.exit(0)

    if args.input == None:
        args.input = "stdin" 
    if args.output == None:
        args.output = "stdout" 

    args.input = open_input(args.input)
    args.output = open_output(args.output)

    if args.r:
        if not is_element_name(args.r, False, args):
            print_err("root-element neobsahuje validni jmeno elementu!")
            sys.exit(30)

    if args.c:
        if not is_element_name(args.c, False, args):
            print_err("column-element neobsahuje validni jmeno elementu!")
            sys.exit(30)

    if args.l:
        if not is_element_name(args.l, False, args):
            print_err("line-element neobsahuje validni jmeno elementu!")
            sys.exit(30)

    if args.i and args.l == None:
        print_err("Vadna kombinace parametru! (-i nebylo zadano s -l)")
        sys.exit(1)

    if args.start != None and (not args.l or not args.i):
        print_err("Vadna kombinace parametru! (--start nebyl zadan s -l a -i)")
        sys.exit(1)

    if args.start != None and args.start < 0:
        print_err("--start = n, n < 0!")
        sys.exit(1)

    if args.missing_field and not args.error_recovery:
        print_err("Vadna kombinace parametru! (--missing-field nebyl zadan s -e, --error_recovery)")
        sys.exit(1)

    if args.all_columns and not args.error_recovery:
        print_err("Vadna kombinace parametru! (--all-columns nebyl zadan s -e, --error_recovery)")
        sys.exit(1)


    if args.s == None:
        args.s = ","
    if args.s == "TAB":
        args.s = "\t" 
    if args.all_columns == None:
        args.all_columns = "col"
    if args.l == None:
        args.l = "row"

    return args;


def parse_csv(csvfile, dlmtr):
    spamreader = None
    try:
        spamreader = csv.reader(csvfile, delimiter=dlmtr, quotechar='"')
        return spamreader
    except csv.Error as e:
        print_err('file {}, line {}: {}'.format(filename, reader.line_num, e))
        sys.exit(4)


def generate_xml(opts, csv):
    # result xml string
    xmlstr = ""
    # copy of rows (need mutable object) 
    rows = copy_rows(csv)

    # replace problematic symbols
    for row in rows:
        i = 0
        for cell in row:
            row[i] = cell.replace("&", "&amp;")
            row[i] = row[i].replace("<", "&lt;")
            row[i] = row[i].replace(">", "&gt;")
            row[i] = row[i].replace("'", "&apos;")
            row[i] = row[i].replace('"', "&quot;")
            i += 1


    # generate XML header if '-n' is not set
    if not opts.n:
        xmlstr += ('<?xml version="1.0" encoding="UTF-8"?>\n')

    # write root element if '-r' is set
    tabs = ""
    if opts.r:
        xmlstr += "<"+opts.r+">\n"
        tabs =TAB

    # first row is header 
    header = None 
    if opts.h:
        if rows:
            header = copy.deepcopy(rows[0])
            id = 0
            for cell in header:
                replace = is_element_name(cell, True, opts)
                if replace: 
                    header[id] = replace
                else:
                    print_err("-h nastaveno, ale nazev elementu zustal nevalidni!")
                    sys.exit(31)
                id += 1
            del rows[0]

    # ident count
    X = 1
    str_replace = opts.h
    if opts.h:
        if header:
            cur_header = iter(header)
    else:
        X = 1

    # row index init
    start = 1
    if opts.start != None:
        start = opts.start

    # first row columns count
    clmn_cnt = None
    if opts.error_recovery:
        if rows:
            if opts.h:
                clmn_cnt = len(header)
            else:
                clmn_cnt = len(rows[0])
            idx = 0
            for row in rows:
                if len(row) > clmn_cnt:
                    if opts.all_columns:
                        pass
                    else:
                        # all columns nenastaveno, zkracuj
                        rows[idx] = row[:clmn_cnt]
                elif len(row) < clmn_cnt:
                    for id in range(clmn_cnt-len(row),len(row)):
                        if opts.missing_field:
                            row.append(opts.missing_field)
                        else:
                            row.append("")

                idx += 1;
    row0_len = None
    if rows:
        row0_len = len(rows[0])

    for row in rows:
        if not opts.error_recovery and row0_len != len(row):
            print_err("Pocet sloupcu na radku neodpovida poctu sloupcu na prvnim radku!")
            sys.exit(32)

        if opts.i:
            xmlstr += tabs+"<"+opts.l+" index="+'"'+str(start)+'"'+">\n"
        else:
            xmlstr += tabs+"<"+opts.l+">\n"

        tabs +=TAB
        idx = 0
        X = 1
        for cell in row:
            if opts.h and idx < len(header):
                xmlstr += tabs+"<"+header[idx]+">\n"
                tabs +=TAB
            elif opts.all_columns or not opts.h:
                xmlstr += tabs+"<"+opts.c+str(X)+">\n"
                tabs +=TAB

            # print column value
            if cell:
                if (opts.h and idx < len(header)) or opts.all_columns or not opts.h:
                    xmlstr += tabs+cell+"\n"

            if opts.h and idx < len(header):
                tabs = tabs[:-4]
                if idx < len(header):
                    xmlstr += tabs+"</"+header[idx]+">\n"
            elif opts.all_columns or not opts.h:
                tabs = tabs[:-4]
                xmlstr += tabs+"</"+opts.c+str(X)+">\n"
            X += 1
            idx += 1
        tabs = tabs[:-4]
        xmlstr += tabs+"</"+opts.l+">\n"
        start += 1

    # root element end tag
    if opts.r:
        xmlstr += "</"+opts.r+">\n"

    return xmlstr

if __name__ == '__main__':
    # get command line arguments
    opts = parse_args()

    # opts.s -- cell separator for csv
    csv = parse_csv(opts.input, opts.s)
    xml = generate_xml(opts, csv)

    # write xml to output file
    opts.output.write(xml)
    sys.exit(0)
