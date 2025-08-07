# Recursive Descent Parsing

## What is recursive descent parsing?

A top-down parser because it starts from the top or outermost grammar rule (here
`expr`) and works its way down into the nested subexpressions before finally
reaching the leaves of the syntax tree. This is in contrast to bottom-up parsers
like LR that start with primary expressions and compose them into larger and
larger chunks of syntax.

It reaches the lowest-precedence expressions first this way, with
higher-precedence operations being handled deeper in the grammar hierarchy.

For 1 + 3 \* 2:

```text
expr()
├─ equality()
   ├─ comparison()
      ├─ term()
         ├─ factor()
         │  ├─ unary()
         │  │  └─ primary() → parses "1"
         │  └─ sees "+", doesn't match ("/" | "*"), returns unary("1")
         └─ sees "+", doesn't match ("/" | "*"), returns factor("1")

         ├─ sees "+", matches ( "-" | "+" ), consumes "+"
         ├─ factor()
         │  ├─ unary()
         │  │  └─ primary() → parses "3"
         │  ├─ sees "*", matches ("/" | "*"), consumes "*"
         │  └─ unary()
         │     └─ primary() → parses "2"
         │  └─ returns unary("3") * unary("2")
         └─ returns factor("1") + factor("3 * 2")
```
