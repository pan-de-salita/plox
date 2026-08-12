# plox

a python implementation of the **lox** language from robert nystrom's *crafting interpreters* — lexer, recursive-descent parser, static resolver, and tree-walking interpreter. pure standard library, no runtime dependencies.

## features

- first-class functions, closures, and lexical scoping
- classes: methods, initializers, `this`, `super`, single inheritance
- `for` / `while` loops, `if` / `else`, logical operators, `print`

## beyond the book

extensions i designed and implemented myself, on top of the textbook:

- **lambda expressions** — anonymous first-class functions:
  ```lox
  var add = fun (a, b) { return a + b; };
  ```
- **ternary operator** — `var max = a > b ? a : b;`
- **`break` statement** for loop control flow
- **unused variable reporting** — the static resolver tracks whether each local variable is ever read and flags unused ones when its scope closes.
- **static methods** — callable on the class itself, not instances:
  ```lox
  class Math {
    class square(n) { return n * n; }
  }
  print Math.square(3); // -> 9
  ```
- **getters** — methods without parentheses, auto-invoked on property access:
  ```lox
  class Circle {
    init(radius) { this.radius = radius; }
    area { return 3.14 * this.radius * this.radius; }
  }
  print Circle(4).area; // -> 50.24
  ```
- **metaclass pattern** — a class is itself an instance. static methods live on an auto-generated `Meta<ClassName>` class, and any instance can introspect itself at runtime via the `klass` and `methods` fields.
- **ast code generation tool** (`tool/generate_ast.py`) — emits the ast node classes and visitor interface from declarative type definitions, instead of writing them by hand.
- also: `%` modulo and the comma operator.

## running

```sh
python lox/lox.py                 # repl
python lox/lox.py path/to/file.lox  # run a script
```

requires python 3.14+ (see `.python-version`).

## layout

- `lox/` — the interpreter: scanner, parser, resolver, interpreter, ast printers
- `tool/` — the ast code generator
- `test.lox` — exploration scripts
