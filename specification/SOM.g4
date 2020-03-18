grammar SOM;

/* This parser accepts valid programs adhering to the following grammar. Comments
and white space are not dealt with in the grammar. Names of non-terminals begin
with a lower-case letter; terminals, with an upper-case one. */

classdef:
    Identifier Equal superclass
    instanceFields method*
    ( Separator classFields method* )?
    EndTerm;

superclass:
    Identifier? NewTerm;

instanceFields:
    ( Or variable* Or )?;

classFields:
    ( Or variable* Or )?;

method:
   pattern Equal ( Primitive | methodBlock );

pattern:
    unaryPattern | keywordPattern | binaryPattern;

unaryPattern:
    unarySelector;

binaryPattern:
    binarySelector argument;

keywordPattern:
    ( keyword argument )+;

methodBlock:
    NewTerm blockContents? EndTerm;

unarySelector:
    identifier;

binarySelector:
    Or | Comma | Minus | Equal | Not | And | Star | Div | Mod | Plus | More |
    Less | At | Per | OperatorSequence;

identifier:
    Primitive | Identifier;

keyword:
    Keyword;

argument:
    variable;

blockContents:
    ( Or localDefs Or )?
    blockBody;

localDefs:
    variable*;

blockBody:
      Exit result
    | expression ( Period blockBody? )?;

result:
    expression Period?;

expression:
    assignation | evaluation;

assignation:
    assignments evaluation;

assignments:
    assignment+;

assignment:
    variable Assign;

evaluation:
    primary messages?;

primary:
    variable | nestedTerm | nestedBlock | literal;

variable:
    identifier;

messages:
      unaryMessage+ binaryMessage* keywordMessage?
    | binaryMessage+ keywordMessage?
    | keywordMessage;

unaryMessage:
    unarySelector;

binaryMessage:
    binarySelector binaryOperand;

binaryOperand:
    primary unaryMessage*;

keywordMessage:
    ( keyword formula )+;

formula:
    binaryOperand binaryMessage*;

nestedTerm:
    NewTerm expression EndTerm;

literal:
    literalArray | literalSymbol | literalString | literalNumber;

literalArray:
    Pound NewTerm
    literal*
    EndTerm;

literalNumber:
    negativeDecimal | literalDecimal;

literalDecimal:
    literalInteger | literalDouble;

negativeDecimal:
    Minus literalDecimal;

literalInteger:
    Integer;

literalDouble:
    Double;

literalSymbol:
    Pound ( string | selector );

literalString:
    string;

selector:
    binarySelector | keywordSelector | unarySelector;

keywordSelector:
    Keyword | KeywordSequence;

string:
    STString;

nestedBlock:
    NewBlock blockPattern? blockContents? EndBlock;

blockPattern:
    blockArguments Or;

blockArguments:
    ( Colon argument )+;

/* Lexer */

Comment:   '"' ~["]* '"' -> skip;
Whitespace : [ \t\r\n]+ -> skip ;

Primitive: 'primitive';
Identifier: [\p{Alpha}] [\p{Alpha}0-9_]*;

Equal: '=';

Separator: '----' '-'*;

NewTerm: '(';
EndTerm: ')';
Or: '|';


Comma: ',';
Minus: '-';
Not:   '~';
And:   '&';
Star:  '*';
Div:   '/';
Mod:   '\\';
Plus:  '+';
More:  '>';
Less:  '<';
At:    '@';
Per:   '%';

OperatorSequence: (
    Not | And | Or | Star | Div |
    Mod | Plus | Equal | More | Less |
    Comma | At | Per | Minus )+;

Colon: ':';

NewBlock: '[';
EndBlock: ']';

Pound:  '#';
Exit:   '^';
Period: '.';
Assign: ':=';

Integer: [0-9]+;
Double: [0-9]+ '.' [0-9]+;

Keyword: Identifier Colon;

KeywordSequence: Keyword+;

STString:
    '\''
    (   '\\t'
      | '\\b'
      | '\\n'
      | '\\r'
      | '\\f'
      | '\\0'
      | '\\\''
      | '\\\\'
      |  ~('\''| '\\')
    )*
    '\'';
