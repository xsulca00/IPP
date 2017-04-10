<?php

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

    const kw_eof = 27;
    const kw_comma = 28;
    const kw_left_parent = 29;
    const kw_right_parent = 30;
    const kw_asterix = 31;
    const kw_semicolon = 32;
    const kw_left_brace = 33;
    const kw_right_brace = 34;
    const kw_tilde = 35;
    const kw_data_type = 36;
    const kw_colon = 37;
    const kw_ident = 38;
    const kw_ampersand = 39;
    const kw_double_colon = 40;
    const kw_access_spec = 41;
}

function ungetc($istream)
{
    fseek($istream, -1, SEEK_CUR);
}

class Token
{
    private $istream = STDIN;
    private $token_name = "";
    private $token_type = Keywords::kw_eof;

    public function __construct($istream)
    {
        $this->istream = $istream;
    }

    public function name()
    {
        return $this->token_name;
    }

    public function type()
    {
        return $this->token_type;
    }

    public function put_back()
    {
        ungetc($this->istream);
    }

    public function get()
    {
        static $keywords = array( 
            "class" => Keywords::kw_class,
            "public" => Keywords::kw_access_spec,
            "protected" => Keywords::kw_access_spec,
            "private" => Keywords::kw_access_spec,
            "using" => Keywords::kw_using,
            "virtual" => Keywords::kw_virtual,
            "static" => Keywords::kw_static,

            "char" => Keywords::kw_data_type,
            "bool" => Keywords::kw_data_type,
            "char16_t" => Keywords::kw_data_type,
            "char32_t" => Keywords::kw_data_type,
            "wchar_t" => Keywords::kw_data_type,
            "signed char" => Keywords::kw_data_type,
            "short int" => Keywords::kw_data_type,
            "int" => Keywords::kw_data_type,
            "long int" => Keywords::kw_data_type,
            "long long int" => Keywords::kw_data_type,
            "unsigned char" => Keywords::kw_data_type,
            "unsigned short int" => Keywords::kw_data_type,
            "unsigned int" => Keywords::kw_data_type,
            "unsigned long int" => Keywords::kw_data_type,
            "unsigned long long int" => Keywords::kw_data_type,
            "float" => Keywords::kw_data_type,
            "double" => Keywords::kw_data_type,
            "long double" => Keywords::kw_data_type,
            "void" => Keywords::kw_data_type,
            "(" => Keywords::kw_left_parent,
            ")" => Keywords::kw_right_parent,
            "*" => Keywords::kw_asterix,
            ":" => Keywords::kw_colon,
            "," => Keywords::kw_comma,
            ";" => Keywords::kw_semicolon,
            "&" => Keywords::kw_ampersand,
            "{" => Keywords::kw_left_brace,
            "}" => Keywords::kw_right_brace,
            "::" => Keywords::kw_double_colon
        );

        for (;;)
        {
            $c = 0;

            while (ctype_space($c = fgetc($this->istream)))
                ;

            if (feof($this->istream))
            {
                $this->token_name = "EOF";
                $this->token_type = Keywords::kw_eof;
                return $this->token_type;
            }

            static $state = "none";

            switch ($c)
            {
                case "=":
                    $state = "pure virtual";
                    break;
                case "0":
                    if ($state == "pure virtual")
                    {
                        $state = "none";
                        $this->token_name = "=0"; 
                        $this->token_type = Keywords::kw_pure_virtual;
                        return $this->token_type;
                    }
                    $this->token_name = $c;
                    break;
                case ":":
                    if ($state == "next colon")
                    {
                        $state = "none";
                        $this->token_name = "::";
                        $this->token_type = Keywords::kw_double_colon;
                        return $this->token_type;        
                    }

                    $state = "next colon";
                    break;
                default:
                    if ($state == "next colon")
                    {
                        ungetc($this->istream);
                        $this->token_type = Keywords::kw_colon;
                        $c = ":";
                    }
                    if ($state == "pure virtual")
                    {
                        ungetc($this->istream);
                        $c = "=";
                    }

                    $state = "none";

                    // identifier ?
                    if (ctype_alpha($c))
                    {
                        $state = "identifier";
                        $id = "";
                        $id = $c;

                        for (;ctype_alnum($c = fgetc($this->istream));)
                            $id = $id.$c;

                        if (!ctype_alnum($c))
                            ungetc($this->istream);

                        static $dtype = "";
                        static $data_types = array( 
                            "signed", "char", "short", "int", "long", "double", "unsigned",
                            "bool", "char16_t", "char32_t", "wchar_t", "float", "void"
                        );

                        if (in_array($id, $data_types))
                        {
                            $dtype .= $id;

                            if (array_key_exists($dtype, $keywords))
                            {
                                $this->token_name = $dtype;
                                $this->token_type = Keywords::kw_data_type;
                                $dtype = "";
                                return $this->token_type;        
                            }
                            $dtype .= " ";
                            break;
                        }
                        else
                        {
                            $dtype = "";
                        }

                        $this->token_name = $id;
                        $this->token_type = (isset($keywords[$id])) ? $keywords[$id] : Keywords::kw_ident;
                        return $this->token_type;        
                    }

                    // normal char
                    $this->token_name = $c;
                    $this->token_type = (isset($keywords[$c])) ? $keywords[$c] : Keywords::kw_ident;
                    return $this->token_type;        
            }
        }
    }
}
?>
