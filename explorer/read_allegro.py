

from __future__ import annotations

import os

from typing import Union, Optional
from explorer.models import *

from enum import Enum

# =============================
#   ERRORS AND HELPER CLASSES
# =============================

class Error(Enum):
    # parse errors
    Expecting_this_got_that = "Expected {}"
    Unexpected_token = "Unexpected token"
    Not_found = "{} {} not found"


class LexerError(Exception):
    def __init__(self, message="unexpected error"):
        self.message = f'{self.__class__.__name__}: {message}'

    def __str__(self) -> str:
        return self.message

class ParserError(Exception):
    def __init__(self, message="unexpected error"):
        self.message = f'{self.__class__.__name__}: {message}'

    def __str__(self) -> str:
        return self.message


class TokenType(Enum):
    # single-character token types
    EQUALS          = '='
    SEMICOLON       = ';'
    COLON           = ':'
    LPAREN          = '('
    RPAREN          = ')'
    COMMA           = ','
    DOT             = '.'
    TICK            = '\''
    # block of reserved words
    FILE_TYPE       = 'FILE_TYPE'
    LIBRARY_PARTS   = 'LIBRARY_PARTS'
    EXPANDEDNETLIST = 'EXPANDEDNETLIST'
    EXPANDEDPARTLIST= 'EXPANDEDPARTLIST'
    PRIMITIVE       = 'PRIMITIVE'
    PIN             = 'PIN'
    PINNUMBER       = 'PIN_NUMBER'      #
    INPUT_LOAD      = 'INPUT_LOAD'      #
    OUTPUT_LOAD     = 'OUTPUT_LOAD'     #
    OUTPUT_TYPE     = 'OUTPUT_TYPE'     #
    BIDIRECTIONAL   = 'BIDIRECTIONAL'   #
    PINUSE          = 'PINUSE'          #
    ENDPIN          = 'END_PIN'
    BODY            = 'BODY'
    PARTNAME        = 'PART_NAME'       #
    JEDECTYPE       = 'JEDEC_TYPE'      #
    CLASS           = 'CLASS'           #
    SWAP_INFO       = 'SWAP_INFO'       #
    VALUE           = 'VALUE'           #
    PARTNUMBER      = 'PART_NUMBER'     #
    ALTSYMBOLS      = 'ALT_SYMBOLS'     #
    ENDBODY         = 'END_BODY'
    ENDPRIMITIVE    = 'END_PRIMITIVE'
    END             = 'END'
    NETNAME         = 'NET_NAME'
    NODENAME        = 'NODE_NAME'
    DIRECTIVES      = 'DIRECTIVES'
    PST_VERSION     = 'PST_VERSION'
    ROOT_DRAWING    = 'ROOT_DRAWING'
    POST_TIME       = 'POST_TIME'
    SOURCE_TOOL     = 'SOURCE_TOOL'
    END_DIRECTIVES  = 'END_DIRECTIVES'
    SECTION_NUMBER  = 'SECTION_NUMBER'
    # misc
    ID              = 'ID'
    STRING          = 'STRING'
    EOF             = 'EOF'
    INVALID         = 'INVALID'


class Token:
    def __init__(self, type: TokenType, value: str, lineno: int, column: int):
        self.type = type
        self.value = value
        self.lineno = lineno
        self.column = column

    def __str__(self):
        """
        String representation of the Token instance.
        Example:
            >>> Token(TokenType.INTEGER, 7, lineno=5, column=10)
            Token(INTEGER, 7, position=5:10)
        """
        return 'Token({type}, {value}, position={lineno}:{column})'.format(
            type=self.type,
            value=repr(self.value),
            lineno=self.lineno,
            column=self.column,
        )

    def __repr__(self):
        return self.__str__()


def _build_reserved_keywords():
    """
    Build a dictionary of reserved keywords.
    """
    tt_list = list(TokenType)
    start_index = tt_list.index(TokenType.FILE_TYPE)
    end_index = tt_list.index(TokenType.SECTION_NUMBER)
    reserved_keywords = {
        token_type.value: token_type
        for token_type in tt_list[start_index:end_index + 1]
    }
    return reserved_keywords


RESERVED_KEYWORDS = _build_reserved_keywords()

# =========
#   LEXER
# =========

class Lexer:

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos]
        self.lineno = 1
        self.column = 1

    def error(self):
        s = "Lexer error on '{lexeme}' line: {lineno} column: {column}".format(
            lexeme=self.current_char,
            lineno=self.lineno,
            column=self.column,
        )
        raise LexerError(message=s)

    def advance(self):
        """Advance the `pos` pointer and set the `current_char` variable."""
        if self.current_char == '\n':
            self.lineno += 1
            self.column = 0

        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = ""  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]
            self.column += 1

    def peek(self):
        pos = self.pos + 1
        if pos > len(self.text) - 1:
            return ""
        else:
            return self.text[pos]

    def skip_whitespace(self):
        while self.current_char != "" and self.current_char.isspace():
            self.advance()

    def _string(self):
        """Handle strings"""

        # Create a new token with current line and column number
        token = Token(TokenType.INVALID, "", self.lineno, self.column)

        value = self.current_char
        self.advance()

        while self.current_char != "":
            if self.current_char == "'" and self.peek() in ['\r','\n',':',',',';']:
                break
            value += self.current_char
            self.advance()

        value += self.current_char
        self.advance()

        token.type = TokenType.STRING
        token.value = value

        return token

    def _id(self):
        """Handle identifiers and reserved keywords"""

        # Create a new token with current line and column number
        token = Token(TokenType.INVALID, "", self.lineno, self.column)

        value = ''
        while self.current_char != "":
            if not self.current_char.isalnum() and self.current_char not in ['_','-']:
                break
            value += self.current_char
            self.advance()

        token_type = RESERVED_KEYWORDS.get(value.upper())
        if token_type is None:
            token.type = TokenType.ID
            token.value = value
        else:
            # reserved keyword
            token.type = token_type
            token.value = value.upper()

        return token

    def next_token(self, ignore_strings:bool=False):
        """
        get the next token. it takes no arguments, or 4 arguments
        In the latter case, next_token() scans the input stream until `until`
        is met. In that case, it returns the `expected` as token.

        THis is used to parse verbatim sections. We know the next token should
        be verbatim. So tell the lexer to keep parsing until the next `}` is
        found. Also does nest in and out. Check the code.
        """
        while self.current_char != "":

            if self.current_char == '{':
                while self.current_char not in ['}' ,'\r', '\n']:
                    self.advance()
                self.advance() # skip the closing }

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == "'" and ignore_strings is False:
                return self._string()

            if self.current_char.isalnum():
                return self._id()

            try:
                # get enum member by value
                token_type = TokenType(self.current_char)
            except ValueError:
                # no enum member with value equal to self.current_char
                self.error()
            else:
                # create a token with a single-character lexeme as its value
                token = Token(token_type, token_type.value, self.lineno, self.column)
                self.advance()
                return token

        # if we r here, its an eof
        return Token(TokenType.EOF, "", self.lineno, self.column)


# ==========
#   PARSER
# ==========

class Parser:

    def __init__(self):
        self.lexer: Lexer | None = None
        self.current_token: Token | None = None
        self.queue_of_tokens = []

        self.parts = dict()

        self.board = Board()

    def error(self, error: Error,
              args: Union[list[str], dict[str,str]]=list(),
              token: Optional[Token] = None
              ):
        """
        raise a parse error.
        Error takes the error code & args which is either a str[], or str<str>
        """
        token = self.current_token if token is None else token
        if isinstance(args, list):
            message = error.value.format(*args)
        else:
            message = error.value.format(**args)

        raise ParserError(f'{token} -> {message}')

    def __call__(self, file):
        self.lexer = Lexer(file.read())
        self.current_token = self.lexer.next_token()

        self.parse_file()

        self.lexer = None
        self.current_token = None

    def consume(self, token_type = None):
        """
        consume the current token.
        Update the parser.current_token with the next token.
        """
        if token_type is not None and self.current_token.type != token_type:
            self.error(Error.Expecting_this_got_that, [token_type])

        if self.queue_of_tokens == []:
            self.current_token = self.lexer.next_token()
        else:
            self.current_token = self.queue_of_tokens.pop(0)

    def peek(self, ith = 1):
        if ith == 0:
            return self.current_token

        while ith > len(self.queue_of_tokens):
            self.queue_of_tokens.append(self.lexer.next_token())
    
        return self.queue_of_tokens[ith-1]

    def parse_file(self):
        self.consume(TokenType.FILE_TYPE)
        self.consume(TokenType.EQUALS)
        if self.current_token.type == TokenType.LIBRARY_PARTS:
            self.parse_pstchip_file()
        elif self.current_token.type == TokenType.EXPANDEDNETLIST:
            self.parse_pstxnet_file()
        elif self.current_token.type == TokenType.EXPANDEDPARTLIST:
            self.parse_pstxprt_file()
        else:
            self.error(Error.Unexpected_token)

    def parse_pstchip_file(self):
        """
        The pstchip.dat file contains a description for each physical part in
        the capture design.
        """
    
        # Unofficial file bnf format follows:
        #
        # pstchip_file := FILE_TYPE = LIBRARY_PARTS ;
        #                 { pstchip_primitive }
        #                 END .
        #
        # pstchip_primitive := PRIMITIVE string ;
        #                      PIN
        #                      [ string : { key_value_dictionary } ]
        #                      END_PIN ;
        #                      BODY
        #                          { key_value_dictionary }
        #                      END_BODY ;
        #                      END_PRIMITIVE ;
        #
        self.consume(TokenType.LIBRARY_PARTS)
        self.consume(TokenType.SEMICOLON)

        while self.current_token.type != TokenType.END:
            self.parse_pstchip_primitive()

        self.consume(TokenType.END)
        self.consume(TokenType.DOT)

    def parse_pstchip_primitive(self):
        self.consume(TokenType.PRIMITIVE)

        identifier = self.current_token.value[1:-1]
        self.consume(TokenType.STRING)
        self.consume(TokenType.SEMICOLON)

        pins = []

        self.consume(TokenType.PIN)
        while self.current_token.type != TokenType.ENDPIN:
            pinname = self.current_token.value[1:-1]
            self.consume(TokenType.STRING)
            self.consume(TokenType.COLON)

            # The pin number(s) for that pin name
            self.consume(TokenType.PINNUMBER)
            self.consume(TokenType.EQUALS)
            pinnumbers = self.current_token.value[2:-2]
            self.consume(TokenType.STRING)
            self.consume(TokenType.SEMICOLON)

            if self.current_token.type == TokenType.INPUT_LOAD:
                self.consume(TokenType.INPUT_LOAD)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                self.consume(TokenType.SEMICOLON)

            if self.current_token.type == TokenType.OUTPUT_LOAD:
                self.consume(TokenType.OUTPUT_LOAD)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                self.consume(TokenType.SEMICOLON)

            if self.current_token.type == TokenType.OUTPUT_TYPE:
                self.consume(TokenType.OUTPUT_TYPE)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                self.consume(TokenType.SEMICOLON)

            if self.current_token.type == TokenType.BIDIRECTIONAL:
                self.consume(TokenType.BIDIRECTIONAL)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                self.consume(TokenType.SEMICOLON)

            if self.current_token.type == TokenType.PINUSE:
                self.consume(TokenType.PINUSE)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                self.consume(TokenType.SEMICOLON)

            # 'If you have a multisection part, then the pin numbers containing
            # that pin name are separated by commas.'
            for pinnumber in pinnumbers.split(','):
                if pinnumber == '0':
                    continue

                pins += [(pinnumber, pinname)]

        self.consume(TokenType.ENDPIN)
        self.consume(TokenType.SEMICOLON)

        package = ''
        self.consume(TokenType.BODY)
        while self.current_token.type != TokenType.ENDBODY:
            if self.current_token.type == TokenType.ID:
                self.consume(TokenType.ID)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                self.consume(TokenType.SEMICOLON)

            self.consume(TokenType.PARTNAME)
            self.consume(TokenType.EQUALS)
            self.consume(TokenType.STRING)
            self.consume(TokenType.SEMICOLON)
            
            self.consume(TokenType.JEDECTYPE)
            self.consume(TokenType.EQUALS)
            package = self.current_token.value[1:-1]
            self.consume(TokenType.STRING)
            self.consume(TokenType.SEMICOLON)
            
            if self.current_token.type == TokenType.CLASS:
                self.consume(TokenType.CLASS)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                self.consume(TokenType.SEMICOLON)
            
            if self.current_token.type == TokenType.SWAP_INFO:
                self.consume(TokenType.SWAP_INFO)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                self.consume(TokenType.SEMICOLON)
            
            if self.current_token.type == TokenType.VALUE:
                self.consume(TokenType.VALUE)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                self.consume(TokenType.SEMICOLON)

            if self.current_token.type == TokenType.PARTNUMBER:
                self.consume(TokenType.PARTNUMBER)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                self.consume(TokenType.SEMICOLON)

            if self.current_token.type == TokenType.ALTSYMBOLS:
                self.consume(TokenType.ALTSYMBOLS)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                self.consume(TokenType.SEMICOLON)

        self.consume(TokenType.ENDBODY)
        self.consume(TokenType.SEMICOLON)
        
        self.consume(TokenType.ENDPRIMITIVE)
        self.consume(TokenType.SEMICOLON)

        self.parts[identifier] = { 'identifier': identifier, 'package': package, 'pins': pins }

    def parse_pstxnet_file(self):
        """
        The pstxnet.dat file is the connectivity file. This file lists every
        net, its properties, its attached nodes, and node properties.
        """
    
        # Unofficial file bnf format follows:
        #
        # pstxnet_file := FILE_TYPE = EXPANDEDNETLIST ;
        #                 { pstxnet_netname }
        #                 END .
        #
        # pstxnet_netname := NET_NAME string
        #                        { key_value_property } ;
        #                    NODE_NAME
        #                    identifier identifier string : string : ;
        #                        { key_value_property }
        #                    END_BODY ;
        #                    END_PRIMITIVE ;
        #
        self.consume(TokenType.EXPANDEDNETLIST)
        self.consume(TokenType.SEMICOLON)

        while self.current_token.type != TokenType.END:
            self.parse_pstxnet_netname()

        self.consume(TokenType.END)
        self.consume(TokenType.DOT)

    def parse_pstxnet_netname(self):
        self.consume(TokenType.NETNAME)

        signal = Signal(self.current_token.value[1:-1])
        self.board.add_signal(signal)
        self.consume(TokenType.STRING)

        # Net canonical path
        self.consume(TokenType.STRING)
        self.consume(TokenType.COLON)

        # Net properties
        while self.current_token.type != TokenType.SEMICOLON:
            self.consume(TokenType.ID)
            self.consume(TokenType.EQUALS)
            self.consume(TokenType.STRING)
            if self.current_token.type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
        self.consume(TokenType.SEMICOLON)

        while self.current_token.type == TokenType.NODENAME:
            self.consume(TokenType.NODENAME)

            component = self.board.get_component(self.current_token.value)
            self.consume(TokenType.ID)

            pin = component.get_pin(self.current_token.value)
            signal.connect(pin)
            self.consume(TokenType.ID)
            self.consume(TokenType.STRING)
            self.consume(TokenType.COLON)
            self.consume(TokenType.STRING)
            self.consume(TokenType.COLON)
            self.consume(TokenType.SEMICOLON)


    def parse_pstxprt_file(self):
        """
        The pstxprt.dat file lists each reference designator and its assigned
        sections
        """

        # Unofficial file bnf format follows:
        #
        # pstxprt_file := FILE_TYPE = EXPANDEDPARTLIST ;
        #                 DIRECTIVES
        #                     { key_value_dictionary } 
        #                 END_DIRECTIVES ;
        #                 { pstxprt_prtname }
        #                 END .
        #
        # pstxprt_prtname := PART_NAME identifier string :
        #                        { key_value_property } ;
        #                    SECTION_NUMBER identifier string :
        #                    identifier identifier string : string : ;
        #                        { key_value_property } ;
        #
        self.consume(TokenType.EXPANDEDPARTLIST)
        self.consume(TokenType.SEMICOLON)

        self.consume(TokenType.DIRECTIVES)
        
        # PST_VERSION directive
        self.consume(TokenType.PST_VERSION)
        self.consume(TokenType.EQUALS)
        if self.current_token.value != "'PST_HDL_CENTRIC_VERSION_0'":
            self.error(Error.Expecting_this_got_that,["'PST_HDL_CENTRIC_VERSION_0'"])
        self.consume(TokenType.STRING)
        self.consume(TokenType.SEMICOLON)

        # ROOT_DRAWING directive
        self.consume(TokenType.ROOT_DRAWING)
        self.consume(TokenType.EQUALS)
        self.board.name = self.current_token.value[1:-1]
        self.consume(TokenType.STRING)
        self.consume(TokenType.SEMICOLON)

        # POST_TIME directive
        self.consume(TokenType.POST_TIME)
        self.consume(TokenType.EQUALS)
        self.consume(TokenType.STRING)
        self.consume(TokenType.SEMICOLON)

        # SOURCE_TOOL directive
        self.consume(TokenType.SOURCE_TOOL)
        self.consume(TokenType.EQUALS)
        self.consume(TokenType.STRING)
        self.consume(TokenType.SEMICOLON)

        self.consume(TokenType.END_DIRECTIVES)
        self.consume(TokenType.SEMICOLON)

        while self.current_token.type != TokenType.END:
            self.parse_pstxprt_prtname()

    def parse_pstxprt_prtname(self):
        self.consume(TokenType.PARTNAME)

        refdes = self.current_token.value
        self.consume(TokenType.ID)

        name = self.current_token.value
        self.consume(TokenType.STRING)
        self.consume(TokenType.COLON)

        while self.current_token.type != TokenType.SEMICOLON:
            self.consume(TokenType.ID)
            self.consume(TokenType.EQUALS)
            self.consume(TokenType.STRING)

            if self.current_token.type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
        self.consume(TokenType.SEMICOLON)

        while self.current_token.type == TokenType.SECTION_NUMBER:
            self.consume(TokenType.SECTION_NUMBER)
            self.consume(TokenType.ID)
            self.consume(TokenType.STRING)
            self.consume(TokenType.COLON)

            while self.current_token.type != TokenType.SEMICOLON:
                self.consume(TokenType.ID)
                self.consume(TokenType.EQUALS)
                self.consume(TokenType.STRING)
                if self.current_token.type == TokenType.COMMA:
                    self.consume(TokenType.COMMA)
            self.consume(TokenType.SEMICOLON)

        part = self.parts[name[1:-1]]
        component = Component(refdes, part['package'])
        for pin in part['pins']:
            component.add_pin(OuterPin(pin[0], pin[1], component))
        self.board.add_component(component)



def read_allegro(folder: str):

    parse = Parser()

    # Allegro netlist folder will consist of these files: pstchip, pstxprt and
    # pstxnet that we each parse in turn
    pstchip_dat = os.path.join(folder, 'pstchip.dat')
    with open(pstchip_dat, 'r') as f:
        
        try:
            parse(f)
        except (ValueError, LexerError, ParserError) as e:
            print(f"Error parsing pstchip.dat: {str(e)}")
            return Board()

    pstxprt_dat = os.path.join(folder, 'pstxprt.dat')
    with open(pstxprt_dat, 'r') as f:
        
        try:
            parse(f)
        except (ValueError, LexerError, ParserError) as e:
            print(f"Error parsing pstxprt.dat: {str(e)}")
            return Board()

    pstxnet_dat = os.path.join(folder, 'pstxnet.dat')
    with open(pstxnet_dat, 'r') as f:
        
        try:
            parse(f)
        except (ValueError, LexerError, ParserError) as e:
            print(f"Error parsing pstxnet.dat: {str(e)}")
            return Board()

    return parse.board
