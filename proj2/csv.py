#!/bin/env python3.6
# -*- coding: utf-8 -*-

import _csv as csv
import sys
import copy
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom

# help message
help_msg= "Skript pro konverzi formátu CSV (viz RFC 4180) do XML. Každému řádku CSV odpovídá jeden dodeﬁnovaný párový element (viz parametr -l) a ten bude obsahovat elementy pro jednotlivé sloupce (viz parametr -h). Tyto elementy pak již budou obsahovat textovou hodnotu dané buňky z CSV zdroje." 


def print_err(*args):
    sys.stderr.write(' '.join(map(str,args)) + '\n')

def copy_rows(csv):
    rows = []
    for row in csv:
        cells = []
        for cell in row:
           cells.append(cell) 
        rows.append(cells)

    return rows


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


    if args.input == None:
        args.input = "stdin" 
    if args.output == None:
        args.output = "stdout" 
    if args.s == None:
        args.s = ","
    if args.all_columns == None:
        args.all_columns = "col"
    if args.l == None:
        args.l = "row"

    print(args)
    return args;

def parse_csv(filename, dlmtr):
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

    spamreader = None
    try:
        spamreader = csv.reader(csvfile, delimiter=dlmtr, quotechar='"')
        return spamreader
    except csv.Error as e:
        sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))

def open_output(name):
    xmlfile = None
    if name == "stdout":
        xmlfile = sys.stdout
    else:
        try:
            xmlfile = open(name, newline='', encoding='utf-8')
        except:
            print_err("Cannot open output file'",name,"'!")
            sys.exit(3)
    return xmlfile

def generate_xml(opts, csv):
    # result xml string
    xmlstr = ""
    # copy of rows (need mutable object) 
    rows = copy_rows(csv)

    # generate XML header if '-n' is not set
    if not opts.n:
        xmlstr += ('<?xml version="1.0" encoding="UTF-8"?>\n')

    # write root element if '-r' is set
    tabs = ""
    if opts.r:
        xmlstr += "<"+opts.r+">\n"
        tabs = "\t"

    # first row is header 
    header = None 
    if opts.h:
        if rows:
            header = copy.deepcopy(rows[0])
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
            clmn_cnt = len(rows[0])
            idx = 0
            for row in rows:
                if len(row) > clmn_cnt:
                    if opts.all_columns:
                        pass
                    else:
                        rows[idx] = row[:clmn_cnt]
                elif len(row) < clmn_cnt:
                    for idx in range(clmn_cnt-len(row)):
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
            print_err("Nespravy pocet sloupcu na radku podle prvniho radku!")
            sys.exit(32)

        if opts.i:
            xmlstr += tabs+"<"+opts.l+" index="+'"'+str(start)+'"'+">\n"
        else:
            xmlstr += tabs+"<"+opts.l+">\n"

        tabs += "\t"
        idx = 0
        X = 1
        for cell in row:
            if opts.h and idx < len(header):
                    xmlstr += tabs+"<"+header[idx]+">\n"
                    tabs += "\t"
            elif opts.all_columns or not opts.h:
                xmlstr += tabs+"<"+opts.c+str(X)+">\n"
                tabs += "\t"
            # print column value
            if cell:
                if (opts.h and idx < len(header)) or opts.all_columns or not opts.h:
                    xmlstr += tabs+cell+"\n"

            if opts.h and idx < len(header):
                tabs = tabs[:-1]
                if idx < len(header):
                    xmlstr += tabs+"</"+header[idx]+">\n"
            elif opts.all_columns or not opts.h:
                tabs = tabs[:-1]
                xmlstr += tabs+"</"+opts.c+str(X)+">\n"
            X += 1
            idx += 1
        tabs = tabs[:-1]
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
    # try open output file
    xmlfile = open_output(opts.output)
    # write xml to output file
    xmlfile.write(xml)
    sys.exit(0)
