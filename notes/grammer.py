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

# New grammar from chapter 8:
#
# program -> statement* EOF
# statement -> expr_stmt
#            | print_stmt
#
# expr_stmt -> expr ";" ;
# print_stmt -> "print" expr ";" ;
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
