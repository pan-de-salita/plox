# Lox's grammar as per ch2
#
# expr -> literals
#       | unary
#       | binary
#       | grouping ;
#
# literal -> STRING | NUMBER | "true" | "false" | "nil" ;
# unary -> ( "-" | "!" ) expr ;
# binary -> expr operator expr ;
# grouping -> "(" expr ")" ;
#
# operator -> "+" | "-" | "*" | "/"
#           | "==" | "!=" | "<" | "<=" | ">" | ">=" ;

# Expansion of 1 + 2 != 4
#
#         binary(!= )
#        /           \
#    binary(+)      lit(4)
#    /   |   \
# lit(1) "+" lit(2)
#
# 0. expression
# 1. binary
# 2. expression operator expression
# 3. binary "!=" expression
# 4. (expression operator expression) "!=" expression
# 5. (literal "+" expression) "!=" expression
# 6. (NUMBER "+" expression) "!=" expression
# 7. (NUMBER "+" literal) "!=" expression
# 8. (NUMBER "+" NUMBER) "!=" expression
# 9. ("1" "+" NUMBER) "!=" expression
# 10. ("1" "+" "2") "!=" expression
# 11. ("1" "+" "2") "!=" literal
# 12. ("1" "+" "2") "!=" NUMBER
# 13. ("1" "+" "2") "!=" "4"

# Limitation of the above grammar:
# Right now, the grammar stuffs all expression types into a single expr rule.
# That same rule is used as the non-terminal for operands, which lets the
# grammar accept any kind of expression as a subexpression, regardless of
# whether the precedence rules allow it. E.g., 1 + 2 * 3 can be parsed as
# any of the following:
#
# - (1 + 2) * 3
# - 1 + (2 * 3)
#
# This can lead to errors in calculations.

# Solution: Stratify the grammar such that each rule can match only the
# expression that are at:
#
# - Its level of precedence
# - A higher level of precedence
#
# - expr -> comma_expr ;
# - comma_expr -> ternary ( "," ternary )* ;
# - ternary -> ( equality "?" equality ":" ternary ) | equality ;
# - equality -> comparison ( ( "!=" | "==" ) comparison )* ;
# - comparison -> term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
# - term -> factor ( ( "-" | "+" ) factor )* ;
# - factor -> unary ( ( "/" | "*" ) unary )* ;
# - unary -> ("-" | "!") unary
#          | primary ;
# - primary -> NUMBER | STRING | "true" | "false" | "nil"
#            | "(" expr ")" ;

# first attempt at a rule for factor:
# - factor -> factor ( "*" | "/" ) unary
#           | unary ;
# NOTE: Lox would have trouble with left-recursive parsing (see how the first
# symbol of the body is the same as the head).

# True ? (True ? x : y) : z

# Updated grammar:
#
# program -> declaration* EOF
#
# declaration  -> fun_decl
#               | var_decl
#               | statement ;
#
# fun_decl     -> "fun" function ;
#
# function     -> IDENTIFIER "(" parameters? ")" block ;
# parameters   -> IDENTIFIER ( "," IDENTIFIER )* ;
#
# var_decl     -> "var" IDENTIFIER ( "=" expr )? ";" ;
#
# statement    -> expr_stmt
#               | while_stmt
#               | for_stmt                          <-- does not need its own node
#               | if_stmt
#               | print_stmt
#               | block;
#
# loop_statement    -> expr_stmt
#                    | while_stmt
#                    | for_stmt
#                    | break_stmt
#                    | if_stmt
#                    | print_stmt
#                    | block;

# expr_stmt     -> expr ";" ;
# while_stmt    -> "while" "(" expr ")" loop_statement ;
# for_stmt      -> "for"
#                  "(" ( var_decl | expr_stmt | ";" ) <-- initializer
#                  expr? ";"                          <-- condition
#                  expr? ")"                          <-- increment
#                  loop_statement ;
# break_stmt    -> "break" ";" ;
# if_stmt       -> "if" "(" expr ")" statement
#                 ( "else" statement )? ;
# print_stmt    -> "print" expr ";" ;
# return_stmt   -> "return" expr? ";" ;
# block         -> "{" declaration* "}" ;
#
# - expr       -> comma ;
# - comma      -> ternary ( "," ternary )* ;
# - assignment -> IDENTIFIER "=" assignment
#               | logic_or;
# - logic_or   -> logic_and ("or" logic_and)* ;
# - logic_and  -> ternary ("and" ternary)* ;
# - ternary    -> ( equality "?" equality ":" ternary ) | equality ;
# - equality   -> comparison ( ( "!=" | "==" ) comparison )* ;
# - comparison -> term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
# - term       -> factor ( ( "-" | "+" ) factor )* ;
# - factor     -> unary ( ( "/" | "*" | "%" ) unary )* ;
# - unary      -> ("-" | "!") unary
#               | call ;
# - call       -> primary ( "(" arguments? ")" )* ;
# - primary    -> NUMBER | STRING
#               | "true" | "false" | "nil"
#               | "(" expr ")"
#               | IDENTIFIER
#               | lambda ;
#
# lambda       -> "fun" "(" parameters* ")" block ;
# arguments    -> expr ( "," expr )* ;
#
# NOTE: There is no place in the grammar where both an expression and a
# are allowed. The operands of, say, + are always expressions, never statments.
# The body of a while loop is always a statement.
#
# Since the two syntaxes are disjoint, we don't need a single base class that
# they all inherit from.

# NOTE: Re If statments:
# The seemingly innocuous optinal else has, in fact, opened up an ambiguity
# in our grammar (see __if_statement() of Parser class). Consider:
#
# if (first) if (second) when_true(); else when_false();
#
# Which if statment does the else clause belong to?
# - If we attach the else to the first if statement, then when_false() is called
#   if first is falsey, regardless of what value second has.
# - If we attach it to the second if statement, then when_false() is only called
#   if first is truthy and second is falsey.
#
# Since else clauses are optional, and there is no explicit delimiter marking the
# end of the if statement, the grammar is ambiguous when you nest ifs in the
# above way. This classic pitfall is called the dangling else problem.
#
# FIX: Most languages and parsers avoid this problem in an ad hoc way. No matter
# what hack they use to get themselves out of the trouble, they always choose
# the same interpretation -- the else is bound to the nearest if that precedes it.
#
# So if (first) if (second) when_true(); else when_false(); would have the else
# clause belong to the second if statement.
#
# NOTE: Re logic_or and logic_and:
# The syntax doesn't care that these expressions short-curcuit. That's a semantic concern.

# NOTE: Desugaring a for loop so we don't need a dedicated for-loop node:
#
# for (var i = 10; i != 0; i = i - 1) print i;
# // Equivalent to:
# {
#     var i = 10;
#     while (i != 0) {
#       print i;
#       i = i - 1;
#     }
# }
#
# for (var i = 10;;) print i;
# // Equivalent to:
# {
#     var i = 10;
#     while (true) {
#         print i;
#     }
# }

# NOTE: Re calls: The name of the function (unless we're using Pascal) isn't
# actualy part of the call syntax. The thing being called -- the callee -- can
# be any expression that evaluates to a function.
