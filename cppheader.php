<?php

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

class Keywords
{
    const kw_class = 0;
    const kw_public = 1;
    const kw_protected = 2;
    const kw_private = 3;
    const kw_using = 4;
    const kw_virtual = 5;
    const kw_static = 6;
    const kw_pure_virtual = 7;

    const kw_char = 8;
    const kw_bool = 9;
    const kw_char16_t = 10;
    const kw_char32_t = 11;
    const kw_wchar_t = 12;
    const kw_signed_char = 13;
    const kw_short_int = 14;
    const kw_int = 15;
    const kw_long_int = 16;
    const kw_long_long_int = 17;
    const kw_unsigned_char = 18;
    const kw_unsigned_short_int = 19;
    const kw_unsigned_int = 20;
    const kw_unsigned_long_int = 21;
    const kw_unsigned_long_long_int = 22;
    const kw_float = 23;
    const kw_double = 24;
    const kw_long_double = 25;
    const kw_void = 26;
}

function printerr($string)
{
    $string .= "\n";
    fwrite(STDERR, $string);
}

function get_token($fin)
{
    $keywords = array( 
        "class" => Keywords::kw_class,
        "public" => Keywords::kw_public,
        "protected" => Keywords::kw_protected,
        "private" => Keywords::kw_private,
        "using" => Keywords::kw_using,
        "virtual" => Keywords::kw_virtual,
        "static" => Keywords::kw_static
    );

    for (;;)
    {
        $c = 0;

        while (ctype_space($c = fgetc($fin)))
            ;

        if (feof($fin))
            return false;

        static $state = "none";

        switch ($c)
        {
            case "=":
                $state = "pure virtual";
                break;
            case "0":
                if ($state == "pure virtual")
                {
                    echo "=0";
                    $state = "none";
                    return true;
                }
                echo $c;
                break;
            case ":":
                if ($state == "next colon")
                {
                    echo "::";
                    $state = "none";
                    return true;
                }

                $state = "next colon";
                break;
            default:
                if ($state == "next colon")
                {
                    fseek($fin, -1, SEEK_CUR);
                    $c = ":";
                }
                if ($state == "pure virtual")
                {
                    fseek($fin, -1, SEEK_CUR);
                    $c = "=";
                }

                $state = "none";
                
                // identifier ?
                if (ctype_alpha($c))
                {
                    $state = "identifier";
                    $id = "";
                    $id = $c;
                    for (;ctype_alnum($c = fgetc($fin));)
                        $id = $id.$c;

                    if (!ctype_alnum($c))
                        fseek($fin, -1, SEEK_CUR);

                    echo "$id";
                    return true;
                }

                // normal char
                echo "$c";
                break;
        }
    }
}

function get_args($arguments)
{
    $patterns = array(
        "/--help/" => "--help",
        "/--input=(.*)/" => "--input",
        "/--output=(.*)/" => "--output",
        "/--pretty-xml=(.*)/" => "--pretty-xml",
        "/--details=(.*)/" => "--details"
    );

    array_shift($arguments);

    $options = array();

    foreach ($arguments as $argument)
    {
        $valid_arg = false;
        foreach ($patterns as $pattern => $option_name)
        {
            $matches = array();
            if (preg_match($pattern, $argument, $matches))
            {
            //    var_dump($matches);
                if (1 < count($matches))
                    $options[$option_name][] = $matches[1];
                else
                    $options[$option_name][] = true;
                $valid_arg = true;
            }
        }
        if (!$valid_arg)
            $options[$argument] = array();
    }

    // print_r($options);
    // find invalid parameters
    foreach ($options as $argument)
    {
        if (empty($argument))
        {
            printerr("Invalid parameter(s) passed!");
            exit(Error_ret::invalid_params);
        }
    }

    return $options;
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
    //
    while (get_token($ifile))
        ;

    fclose($ifile);
    fclose($ofile);

}

exit(Error_ret::no_error);
?>
