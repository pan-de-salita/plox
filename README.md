# plox

A Python implementation of the **Lox** language from Robert Nystrom's *Crafting Interpreters* — lexer, recursive-descent parser, static resolver, and tree-walking interpreter. Pure standard library, no runtime dependencies.

## Features

- First-class functions, closures, and lexical scoping
- Classes: methods, initializers, `this`, `super`, single inheritance
- `for` / `while` loops, `if` / `else`, logical operators, `print`

## Beyond the book ✨

Extensions I designed and implemented myself, on top of the textbook:

- **Lambda expressions** — anonymous first-class functions:
  ```lox
  var add = fun (a, b) { return a + b; };
  ```
- **Ternary operator** — `var max = a > b ? a : b;`
- **`break` statement** for loop control flow
- **Static methods** — callable on the class itself, not instances:
  ```lox
  class Math {
    class square(n) { return n * n; }
  }
  print Math.square(3); // -> 9
  ```
- **Getters** — methods without parentheses, auto-invoked on property access:
  ```lox
  class Circle {
    init(radius) { this.radius = radius; }
    area { return 3.14 * this.radius * this.radius; }
  }
  print Circle(4).area; // -> 50.24
  ```
- **Metaclass pattern** — a class is itself an instance. Static methods live on an auto-generated `Meta<ClassName>` class, and any instance can introspect itself at runtime via the `klass` and `methods` fields.
- **AST code generation tool** (`tool/generate_ast.py`) — emits the AST node classes and Visitor interface from declarative type definitions, instead of writing them by hand.
- **RPN AST printer** (`lox/ast_printer_rpn.py`) — a second visitor that renders expressions in Reverse Polish Notation, alongside the book's parenthesized printer.
- Also: `%` modulo and the comma operator.

## Running

```sh
python lox/lox.py                 # REPL
python lox/lox.py path/to/file.lox  # run a script
```

Requires Python 3.14+ (see `.python-version`).

## Layout

- `lox/` — the interpreter: scanner, parser, resolver, interpreter, AST printers
- `tool/` — the AST code generator
- `test.lox` — exploration scripts