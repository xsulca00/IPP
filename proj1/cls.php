<?php

include_once "args.php";
include_once "lex.php";
include_once "parser.php";

$writer = new XMLWriter();

class Error_ret
{
    // no error
    const no_error = 0;
    // invalid parameter format or bad combination of parameters
    const invalid_params = 1;
    // input file does not exist or input file opening in read mod failed
    const opening_input = 2;
    // output file opening error due to lack of privileges or existing file 
    const opening_output = 3;
    // bad input file format
    const input_file_format = 4;
    // 10 - 99 task specfic error return value
    const bad_indent_value = 10;
    // ...
    // 100 - 127 
}

function printerr($string)
{
    $string .= "\n";
    fwrite(STDERR, $string);
}

function get_opt($name, $options)
{
    // program parameter passed
    if (array_key_exists($name, $options))
    {
        // the same program parameter typed more than once
        if (2 <= count($options[$name]))
        {
            printerr("Parameter '$name' typed more than once!");
            exit(Error_ret::invalid_params); 
        }
        return $options[$name][0];
    }
    return false;
}

$options = get_args($argv);

// priority - just help first...
if (get_opt("--help", $options))
{
    $prompter = "Nápověda:\n    • --input=ﬁle\n\tVstupní textový soubor ﬁle, který obsahuje popis tříd jazyka C++ podle popsaných omezení.\n\tChybí-li tento parametr, je uvažován standardní vstup.\n
    • --output=ﬁle\n\tVýstupní soubor ﬁle ve formátu XML v kódování UTF-8.\n\tNení-li tento parametr zadán, bude výstup vypsán na standardní výstup.\n
    • --pretty-xml=k\n\tVýstupní XML bude formátováno tak, že každé nové zanoření bude odsazeno o k mezer oproti předchozímu.\n\tNení-li k zadáno, uvažujte k = 4.\n\tPokud tento parametr není zadán, je formátování výstupního XML volné.\n
    • --details=class\n\tMísto stromu dědičností mezi třídami se na výstup vypisují údaje o členech třídy se jménem class.\n\tPokud argument class není zadán, vypisují se detaily o všech třídách v daném souboru, kde kořenem XML souboru je model.\n\tPokud class neexistuje, bude na výstup vypsána pouze XML hlavička.\n";
        // other parameters were passed?
    if (2 <= count($options))
    {
        printerr("Other parameters were passed, not only '--help'!");
        exit(Error_ret::invalid_params);
    }
    echo "$prompter\n"; 
}
else
{
    $k = 4;             // default is 4
    $ifile = STDIN;     // input
    $ofile = STDOUT;    // output
    $dtlclass = NULL;   // detailed class

    if ($indent = get_opt("--pretty-xml", $options))
    {
        // is string integer?
        for($len = strlen($indent), $i = 0; $i != $len; $i++) 
        {
            // does not need to check '-', need non-negative
            if (!ctype_digit($indent[$i]))
            {
                printerr("Invalid indent value '$indent'!");
                exit(Error_ret::bad_indent_value);
            }
        }
        $k = (int)$indent;
    }
   
    // empty string is implicitly converted to false
    if ($op_dtlclass = get_opt("--details", $options))
    {
        $dtlclass = $op_dtlclass;
    }

    if ($fname = get_opt("--input", $options))
    {
        if (is_dir($fname))
        {
            printerr("Input file '$fname' is a directory!");
            exit(Error_ret::opening_input);
        }

        $ifile = fopen($fname, "r"); 

        if (!$ifile)
            exit(Error_ret::opening_input);
    }

    if ($fname = get_opt("--output", $options))
    {
        $ofile = fopen($fname, "w");

        if (!$ofile)
            exit(Error_ret::opening_output);
    }

    //echo "$k\n$ifile\n$ofile\n$dtlclass\n";

    // details=  -- not set
    // info about all classes
    // details option missing => class doesnt exist -> just print header
    
    // pretty xml opt missing => whatever format
    // k is 4 in default
    $token_stream = new Token($ifile);

    global $writer;

    $writer->openMemory();
    $writer->setIndent(true);

    $indent = "";
    while ($k--)
        $indent .= " ";
    $writer->setIndentString($indent);
    $writer->startDocument("1.0", "UTF-8");
    $writer->startElement('model');

    parse_class($token_stream, $ofile, $dtlclass);

    if (!$dtlclass)
        Class_obj::print_all();

    $writer->endElement();
    $writer->endDocument();
    fwrite($ofile, $writer->outputMemory());

    fclose($ifile);
    fclose($ofile);
}

exit(Error_ret::no_error);
?>
