# Guillemot
**Guillemot** is a probabilistic programming language designed for binary, discrete, and discretized continuous distributions (continuous distributions are not supported). It supports both exact (direct search) (except when including multiplication, division, or exponentiation operations, or weighted least squares regression) and approximate (random sampling) inference.

Additonally, Guillemot allows commands to marginalize expressions (including variables) or eliminate certain remaining variables, improving program runtime.

![Guillemot logo](images/logo.png?raw=true)


## Assumptions

1. Properly formatted Guillemot program as input.
2. A *return* statement must occur within the program.


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

5. Search space reduction
    * Expression marginalization
    * Variable elimination

6. Show circuit

7. Weighted Least Squares Regression




## Setup

Guillemot can be used directly from this directory or through Docker. Both are described below:

1. **Direct setup**

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
* numpy
* scipy


These may be installed via (may require *sudo* access):
```bash
pip3 install matplotlib numpy scipy
```

Run Guillemot on a *.glmt* file (use the *-T* flag after the filename to show the time in miliseconds):
```bash
alias guillemot="python3 main.py"

# Exact inference (direct search)
guillemot enumerate benchmarks/truck_engine.glmt

# Approximate inference (random sampling)
guillemot rejection benchmarks/truck_engine.glmt
```


2. **Docker setup**

Note: Docker images do not have GUI access, so the circuit cannot be shown. All other commands work as expected.

Build image using Docker, this step may require sudo access:

```bash
docker build -t guillemot/guillemot:latest .
```

Enter the image (note, the container will be deleted after exiting), this step may require sudo access:
```bash
docker run -it --rm guillemot/guillemot:latest bash
```

Run a provided benchmark (use the *-T* flag after the filename to show the time in miliseconds):
```bash
# Exact inference (direct search)
guillemot enumerate benchmarks/truck_engine.glmt

# Approximate inference (random sampling)
guillemot rejection benchmarks/truck_engine.glmt
```




## Examples
Multiple examples are provided within the *benchmarks/* directory.



## References

Available in *references.md* as well as in the code. In the case of a code piece utilized multiple times but only used from another resource once (e.g. a stack overflow reference), only the first time is mentioned.
