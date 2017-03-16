<?php
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
?>
