# A Map of the Territory

I visualize the network of paths an implementation may choose as climbing a
mountain. You start off at the bottom with the program as raw source text,
literally just a string of characters. Each phase analyzes the program and
transforms it to some higher-level representation where the semantics -- what
the author wants the computer to do -- become more apparent.

Eventually we reach the peack. We have a bird's-eye view of the user's program
and can see what their code means. We begin our descent down the other side of
the mountain. We transform this higher-level representation down to successively
lower-level forms to get closer and closer to something we know how to make the
CPU actually execute.

```
`var average = (min + max) / 2;`
```

## Step 1: Scanning (or Lexing, aka Lexical Analysis)

The process where the language's scanner takes in a linear stream of characters
and chunks them together into a series of "words", or, more formally, "tokens".

```
- var
- average
- =
- (
- min
- +
- max
- )
- /
- 2
- ;
```

## Step 2: Parsing

This is where our syntax gets a grammer -- the ability to compose larger
expressions and statementss out of smaller parts. At this stage, the languge's
parser takes the flat sequence of tokens and builds a tree structure that
mirrors the nested nature of the grammar.

This trees are called parse trees or abstract syntax trees (ASTs)

```
        Stmt.Var [average]
                     |
        Expr.Binary [/]
                    / \
      Expr.Binary [+] [2] Expr.Literal
                  /     \
 Expr.Variable [min]   [max] Expr.Variable
```

A parser should also be able to report syntax errors.

## Step 3: Static Analysis

The analysis of a program without executing it. This involves binding/resolution
or identifiers, determination of scope, type validation (in typed languages),
etc. The semantic insight gained is then stored in any of the following:

- As attributes on the syntax tree itself (extra fields in the nodes that aren't
initialized during parsing but get filled in later
- A lookup table (a symbol table)
- Transforming the tree into an entirely new data structure that more directly
expresses the semantics of the code

#### NOTE Everthing up to this point is considered the frontend of a language.
