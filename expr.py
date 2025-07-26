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
