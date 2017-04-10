#!/bin/env python3.6
# -*- coding: utf-8 -*-

import _csv as csv
import argparse
import sys

# help message
help_msg= "Skript pro konverzi formátu CSV (viz RFC 4180) do XML. Každému řádku CSV odpovídá jeden dodeﬁnovaný párový element (viz parametr -l) a ten bude obsahovat elementy pro jednotlivé sloupce (viz parametr -h). Tyto elementy pak již budou obsahovat textovou hodnotu dané buňky z CSV zdroje." 


def print_err(*args):
    sys.stderr.write(' '.join(map(str,args)) + '\n')

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
                        nargs="?",
                        const=True,
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
                        default=1,
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
        sys.exit(1)

    if args.help:
        if len(sys.argv) > 2:
            print_err("Zadano vice argumentu spolu s --help!")
            sys.exit(1)
        parser.print_help()
        sys.exit(0)

    if args.start < 0:
        print_err("Vadna kombinace parametru!")
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

    if args.i and args.l == None:
        print_err("Vadna kombinace parametru!")
        sys.exit(1)

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

def generate_xml(filename):
    # try open output file
    xmlfile = None
    if filename == "stdout":
        xmlfile = sys.stdout
    else:
        try:
            xmlfile = open(filename, newline='', encoding='utf-8')
        except:
            print_err("Cannot open output file'",filename,"'!")
            sys.exit(3)

if __name__ == '__main__':
    opts = parse_args()
    # opts.s -- cell separator for csv
    csv = parse_csv(opts.input, opts.s)
    generate_xml(opts.output)
    for row in csv:
        print(row)
