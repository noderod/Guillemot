# Summary
**Guillemot** is a probabilistic programming language designed for binary, discrete, and discretized continuous distributions (continuous distributions are not supported). It supports both exact (search) and approximate (random sampling) inference.

Additonally, Guillemot allows commands to marginalize expressions (including variables) or eliminate certain remaining variables, improving program runtime.


## Assumptions

1. Properly formatted Guillemot program as input
2. A *return* statement must occur within the program, but one or more *observation* statements are not required.


## Supported operations

1. Logical operators:
    * Equality (==)
    * Not equality (!=)
    * Greater than (>)
    * Greater than or equal (>=)
    * Greater than (>)
    * Greater than or equal (>=)

2. Variable calculation operations:
    * Expectation
    * Variance

3. Variable types supported:
    * Binary (implemented internally as a discrete numeric)
    * Discrete:
        * Numeric: Each state must be a number, either an integer or a float
        * Qualitative: Each state must be a string
    * Continuous (discretized), the following distributions are supported:
        * Beta
        * Gaussian (Normal)
        * Pareto
        * Uniform





## Setup




## Usage


## Examples
Multiple examples are provided within the *benchmarks/* directory.



## References

Available in *references.md* as well as in the code. In the case of a code piece utilized multiple times but only used from another resource once (e.g. a stack overflow reference), only the first time is mentioned.
