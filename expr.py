# Lox's grammar as per ch2
#
# expr -> literals
#       | unary
#       | binary
#       | grouping ;
#
# literal -> STRING | NUMBER | "true" | "false" | "nil" ;
# unary -> ( "-" | "!" ) expr;
# binary -> expr operator expr;
# grouping -> "(" expr ")";
#
# operator -> "+" | "-" | "*" | "/"
#           | "==" | "!=" | "<" | "<=" | ">" | ">=";
