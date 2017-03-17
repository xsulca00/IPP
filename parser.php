<?php
//////////////////////////////////
/// PARSER
//
class Member_func
{
    public $type; // destructor or constructor

    public $virtual;
    public $ret_type;
    public $name;
    public $args;
    public $pure;

    public $defined;

    function __construct($type, $virtual, $ret_type, $name, $args, $pure, $defined)
    {
        $this->type = $type;
        $this->virtual = $virtual;
        $this->ret_type = $ret_type;
        $this->name = $name;
        $this->args = $args;
        $this->pure = $pure;
        $this->defined = $defined;
    }
}

class Data_member
{
    public $type; // static ...
    public $data_type;
    public $name;

    function __construct($type, $data_type, $name)
    {
        $this->type = $type;
        $this->data_type = $data_type;
        $this->name = $name;
    }
}

function deeper($derived, &$functions)
{
    foreach($derived as $dclass)
    {
        foreach ($dclass->member_funcs() as $method)
        {
            $functions[] = $method;
//            echo "FUNC: ".$method->name."\n";
        }

        if (!empty($dclass->derived()))
        {
            deeper($dclass->derived(), $functions);
        }
    }
}

class Class_obj
{
    private $name;
    private $derivations;
    private $abstract;
    private $member_funcs;
    private $data_members;

    static public $inheritance = array(); 
    static public $classes = array(); 

    function __construct($name)
    {
        $this->name = $name;
        $this->abstract = false;

        self::$inheritance[$name] = array();
        self::$inheritance[$name][] = $this;

        $this->derivations = array();
        $this->member_funcs = array();
        $this->data_members = array();
        // echo "\nIN: ".self::$inheritance[$name]->name()."\n";
    }

    public function add_mem_func($type, $virtual, $ret_type, $name, $args, $pure, $defined)
    {
        if (isset($this->functions[$name]) && $this->functions[$name]->defined)
        {
            printerr("Redefinition of '$name' func in '$this->name' class!");
            exit(Error_ret::input_file_format);
        }
            
        $this->member_funcs[$name] = new Member_func($type, $virtual, $ret_type, $name, $args, $pure, $defined);
    }

    public function add_data_mem($type, $data_type, $name)
    {
        if (isset($this->data_members[$name]))
        {
            printerr("Redefinition of '$name' data member in '$this->name' class!");
            exit(Error_ret::input_file_format);
        }
        $this->data_members[$name] = new Data_member($type, $data_type, $name);
    }

    public function functions()
    {
        return $this->member_funcs;
    }

    public function member_funcs()
    {
        return $this->member_funcs;
    }

    public function func_defined($name)
    {
        return $this->functions[$name]->defined;
    }

    public function set_abstract()
    {
        $this->abstract = true;
    }

    public function is_abstract()
    {
        return $this->abstract;
    }

    public static function is_defined($class_name)
    {
        if (!array_key_exists($class_name, self::$classes))
        {
            return false;
        }
        return true;
    }

    public static function print_all()
    {
        global $writer;
        static $visited = array(); 

        function traverse($array, &$visited)
        {
            global $writer;
            $base = array_shift($array); 
            $base_name = $base->name();

            $writer->startElement("class");
            $writer->writeAttribute("name", $base_name);
            $writer->writeAttribute("kind", ($base->is_abstract()) ? "abstract" : "concrete");

            while ($cname = array_shift($array))
            {
                $name = $cname->name();
                $visited[$name] = true;

                if (Class_obj::$inheritance[$name])
                    traverse(Class_obj::$inheritance[$name], $visited);
            } 
            $writer->endElement();
        }

        foreach (self::$inheritance as $derived_array)
        {
            $base = $derived_array[0];
            if (!isset($visited[$base->name()]))
                traverse($derived_array, $visited);
        }
    }

    public function derived()
    {
        return $this->derivations;
    }


    public function get_pure_func()
    {
        $functions = array();

        if (!empty($this->derivations))
            deeper($this->derivations, $functions);

        return $functions;
    }

    public function check_abstract()
    {
        $pure_methods = $this->get_pure_func();

        print_r($pure_methods);
    }

    public function define()
    {
        $class_name = $this->name;
        if (self::is_defined($class_name))
        {
            printerr("Redefinition of class '$class_name'!");
            exit(Error_ret::input_file_format);
        }
        self::$classes[$class_name] = $this; 
    }

    public function name()
    {
        return $this->name;
    }

    public function derivations()
    {
        return $this->derivations();
    }

    public function derived_from($base_name)
    {
        if (!self::is_defined($base_name))
        {
            printerr("Undefined class '$class_name'!");
            exit(Error_ret::input_file_format);
        }

        $base = self::$classes[$base_name];

        $this->abstract = $base->is_abstract();
        $this->derivations[$base_name] = $base;

        //print_r($this->derivations);

        self::$inheritance[$base_name][] = $this;
    }
}

////////////////////////////
// PARSING FUNCTIONS

// parsing according to respective grammar
//

function parse_class($token, $ofile)
{
    for (;;)
    {
//        global $writer;
        // class keyword
        $token->get();

        switch ($token->type())
        { 
            case Keywords::kw_class:
                echo $token->name();

                // class name
                $token->get();
                $class_name = $token->name();

                $class = new Class_obj($class_name);
                /*
                $writer->startElement("class");
                $writer->writeAttribute('name', $class_name);
                $writer->writeAttribute('kind', 'concrete');
                $writer->endElement();
                 */

                echo " $class_name";

                // public by default when inheritance type is left out
                $token->get();

                // access specifiers (inheritance) ?
                if ($token->type() == Keywords::kw_colon)
                {
                //    $writer->startElement('inheritance');
                    echo " :";
                    parse_access_specifier($token, $ofile, $class);
                 //   $writer->endElement();
                }

                if ($token->type() == Keywords::kw_left_brace)
                {
                    // body of the class
                    echo "\n{\n";
                    parse_expression_type_list($token, $ofile, $class);
                    echo "};\n\n";

                    // class is fully defined, record that
                    $class->define();
                    $class->check_abstract();
                    //$class->check_abstract();
                    //eat semicolon
                    $token->get();
                    ////print_r($class->functions());
                }
                break;
            default:
                return;
        }
    }
}

function parse_access_specifier($token, $ofiles, $class)
{
    {
        // public, protected, private
        $token->get();
        /*
        global $writer;

        $writer->startElement('from');
         */

        $access = "private";
        $base_name = "";

        if ($token->type() == Keywords::kw_access_spec)
        {
            // ok, access specifier explicitly set
            $access = $token->name();
            echo " $access";
            // eat access specifier
            $token->get();
        }

        // inherited class name
        $base_name = $token->name();

        $class->derived_from($base_name);
/*
        $writer->writeAttribute('name', $cname);
        $writer->writeAttribute('privacy', $access);
 */

        echo " $base_name";
        /*
        global $class_names;
        if (!$class_names->is_defined($cname))
        {
            printerr("Undefined class: $cname !");
            exit(Error_ret::input_file_format);
        }
         */

  //      $writer->endElement();
    }

    for (;;)
    {
        $token->get();

        if ($token->type() == Keywords::kw_comma)
        {
            echo ",";
            //$writer->startElement('from');
            $access = "private";
            $base_name = "";

            $token->get();
            // public, protected, private
            if ($token->type() == Keywords::kw_access_spec)
            {
                $access = $token->name();
                echo " $access";
                $token->get();
            }

            // inherited class name
            $base_name = $token->name();

            $class->derived_from($base_name);

            echo " $base_name";
/*
            $writer->writeAttribute('name', $cname);
            $writer->writeAttribute('privacy', $access);
 */
            /*
            if (!$class_names->is_defined($cname))
            {
                printerr("Undefined class: $cname !");
                exit(Error_ret::input_file_format);
            }
             */
  //          $writer->endElement();
        }
        else
        {
            break;
        }
    }
}

function parse_expression_type_list($token, $ofile, $class)
{
    static $elem_end = false;
    for (;;)
    {
        //global $writer;
        $token->get();

        // member access specifier
        switch ($token->type())
        {
            case Keywords::kw_access_spec:
                $access = $token->name();
                if ($elem_end)
                {
         //           $writer->endElement();
                    $elem_end = false;
                }
                else
                {
          //          $writer->startElement($access);
                }
                $elem_end = true;
                echo "  $access:\n";
                // eat colon
                $token->get();
                break;
            case Keywords::kw_static:
            case Keywords::kw_data_type:
            case Keywords::kw_virtual:
                parse_member_definition($token, $ofile, $class);
                break;
            case Keywords::kw_using:
                $token->get();
                // first ID
                $first_id = $token->name();
                // eat first ID 
                $token->get();
                // eat double colon
                $token->get();
                // second ID
                $second_id = $token->name();
                echo "using $first_id::$second_id;";
                // eat second ID
                $token->get();
                break;
            default:
                if ($elem_end)
                {
           //         $writer->endElement();
                    $elem_end = false;
                }
                return;
        }
    }
}

function parse_member_definition($token, $ofile, $class)
{
    $mem_specifier = "";
    $data_speicifier = "";
    $mem_modifier = "";
    $identifier = "";

    echo "  ";
    $virtual = false;
    $static = false;

    if ($token->type() == Keywords::kw_static ||
        $token->type() == Keywords::kw_virtual)
    {
        if ($token->type() == Keywords::kw_static)
        {
            $static = true;
            echo "static ";
        }
        else
        {
            $virtual = true;
            echo "virtual ";
        }

        $mem_specifier = $token->name();
        $token->get();
    }

    $data_type = $token->name();
    echo "$data_type";
    $token->get();

    if ($token->type() == Keywords::kw_asterix ||
        $token->type() == Keywords::kw_ampersand ||
        $token->type() == Keywords::kw_tilde)
    {
        $mem_modifier = $token->name();
        echo "$mem_modifier ";
        $token->get();
    }

    if ($data_type != "void")
    {
        $identifier = $token->name();
        echo "$identifier";
        $token->get();
    }

    //TODO: semantic redefinition variable, void variable
    parse_member_definition_more($token, $ofile, $class, $identifier, $virtual, $data_type, $mem_modifier , $static);
}

function parse_member_definition_more($token, $ofile, $class, $identifier, $virtual, $data_type, $mem_modifier , $static)
{
    switch ($token->type())
    {
        // data member
        case Keywords::kw_semicolon:
            echo ";\n";
            $class->add_data_mem($static, $data_type." $mem_modifier", $identifier);
            break;
        // member function
        case Keywords::kw_left_parent:
            echo "(";
            // function has arguments? process them!
            if ($token->type() != Keywords::kw_right_parent)
            {
                parse_argument_list($token, $ofile, $class);
            }

            $args = "void";
            echo ")";
            // eat closing parenthes
            $token->get();

            $fun_name = $identifier;
            $pure = false;
            $defined = false;
            switch ($token->type())
            {
                case Keywords::kw_semicolon:
                    echo $token->name();
                    break;
                case Keywords::kw_pure_virtual:
                    echo " = 0"; 
                    $class->set_abstract();
                    $pure = true;
                    // eat =0 
                    $token->get();
                    echo $token->name();
                    break;
                case Keywords::kw_left_brace:
                    // eat {
                    $token->get();
                    // eat } 
                    $token->get();
                    echo "{ }\n";

                    // function defined
                    $defined = true;

                    if ($token->type() == Keywords::kw_semicolon)
                    {
                        echo $token->name();
                    }
                    else
                    {
                        $token->put_back();
                    }
                    break;
                default:
                    echo "ERROR!";
                    break;
            }
            $type = "static";
            if ($mem_modifier == "~")
                $type = "destructor";
            elseif ($class->name() == $fun_name)
                $type = "constructor";

            $class->add_mem_func($type, $virtual, $data_type." $mem_modifier", $fun_name, $args, $pure, $virtual, $defined);
            break;
    }
}

function parse_argument_list($token, $ofile, $class)
{
    $token->get();

    // function arguments
    parse_member_definition($token, $ofile, $class);

    if ($token->type() == Keywords::kw_right_parent)
        return;

    for (;;)
    {
        $token->get();

        if ($token->type() == Keywords::kw_comma)
        {
            echo ", ";
            parse_member_definition($token, $ofile, $class);
        }
        else
        {
            break;
        }
    }
}
//////////////////////////////////
?>
