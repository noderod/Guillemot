# Summary
**Guillemot** is a probabilistic programming language designed for binary, discrete, and discretized continuous distributions (continuous distributions are not supported). It supports both exact (direct search) (except when including multiplication, division, or exponentiation) and approximate (random sampling) inference.

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

2. Arithmetic operations:
    * Addition (A + B)
    * Substraction (A - B)
    * Multiplication (A \* B)
    * Division (A / B)
    * Exponentiation (A \*\* B)
    * Opposite (- A)

3. Variable calculation operations:
    * Expectation
    * Variance

4. Variable types supported:
    * Binary (implemented internally as a discrete numeric)
    * Discrete:
        * Numeric: Each state must be a number, either an integer or a float
        * Qualitative: Each state must be a string
    * Continuous (discretized), the following distributions are supported:
        * Beta
        * Gaussian (Normal)
        * Pareto
        * Uniform

5. Show circuit




## Setup

Guillemot can be used directly after cloning this directory via:

```bash
git clone https://github.com/noderod/Guillemot.git
```

Enter the directory:

```bash
cd Guillemot/
```

If not already installed, the following python3 libraries are required:
* matplotlib
* networkx
* numpy
* scipy


These may be installed via (may require *sudo* access):
```bash
pip3 install matplotlib numpy scipy
```




## Usage


Run Guillemot on a *.glmt* file (use the *-T* flag after the filename to show the time in miliseconds):
```bash
alias guillemot="python3 main.py"

# Exact inference (direct search)
guillemot enumerate benchmarks/truck_engine.glmt

# Approximate inference (random sampling)
guillemot rejection benchmarks/truck_engine.glmt
```




## Examples
Multiple examples are provided within the *benchmarks/* directory.



## References

Available in *references.md* as well as in the code. In the case of a code piece utilized multiple times but only used from another resource once (e.g. a stack overflow reference), only the first time is mentioned.
