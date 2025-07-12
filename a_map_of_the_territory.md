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

__Our program__
`var average = (min + max) / 2;`

## Step 1: Scanning (or Lexing, aka Lexical Analysis)

The process where the language's scanner takes in a linear stream of characters
and chunks them together into a series of "words", or, more formally, "tokens".

__Our program scanned__
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
