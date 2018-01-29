# Nemo: Multi-Criteria Test-Suite Minimization with Integer Nonlinear Programming

Jun-Wei Lin, Reyhaneh Jabbarvand, Joshua Garcia, and Sam Malek

International Conference of Software Engineering (ICSE 2018), Gothenburg, Sweden, May 2018. (21% acceptance rate).

## Prerequisite

* Python 2.7
* Installed ILP solvers such as [CPLEX](https://www-01.ibm.com/software/commerce/optimization/cplex-optimizer/)
or [lp_solve](http://lpsolve.sourceforge.net/5.5/)
if you want to run them locally. 
Alternatively, you can run solvers on [NEOS server](https://neos-server.org/neos/)

## Getting started

### Formulate the problem using Linear approach (LF_LS)

```bash
$ python formulator.py example config.linear.json  # will generate linear.cplex.lp
# Solve the model locally or using service on NEOS
$ cplex -c "read example/linear.cplex.lp" "optimize" "display solution variables -" "quit" > example/linear.sol.cplex
python generator.py example linear.sol.cplex 
Minimized test suite: ['t2', 't3']
# Minimized test suite: 2
# Statements by original suite: 3
# Statements by minimized suite: 3
# Faults by original suite: 4
# Faults by minimized suite: 3
# Running time by original suite: 3
# Running time by minimized suite: 2
```

### Formulate the problem using Nemo-Aux (NF_LS)

```bash
$ python formulator.py example config.nemo-aux.json  # will generate nemo-aux.cplex.lp
# Solve the model locally or using service on NEOS
$ cplex -c "read example/nemo-aux.cplex.lp" "optimize" "display solution variables -" "quit" > example/nemo-aux.sol.cplex
$ python generator.py example nemo-aux.sol.cplex 
Minimized test suite: ['t2', 't1']
# Minimized test suite: 2
# Statements by original suite: 3
# Statements by minimized suite: 3
# Faults by original suite: 4
# Faults by minimized suite: 4
# Running time by original suite: 3
# Running time by minimized suite: 2
```

### Formulate the problem using Nemo-Nonlinear (NF_NS)

```bash
$ python formulator.py example config.nemo-nonlinear.json  # will generate nemo-nonlinear.ampl
# Solve the nonlinear model using Couenne on NEOS, and save the result in nemo-nonlinear.sol.couenne
$ python generator.py example nemo-nonlinear.sol.couenne
Minimized test suite: ['t2', 't1']
# Minimized test suite: 2
# Statements by original suite: 3
# Statements by minimized suite: 3
# Faults by original suite: 4
# Faults by minimized suite: 4
# Running time by original suite: 3
# Running time by minimized suite: 2
```

## Test-related data

```bash
$ cd example
$ cat cov.info      # statement coverage
t1:1
t2:2 3
t3:1 3
$ cat fault.info    # fault coverage
t1:4
t2:1 2 3
t3:1 2 3
$ cat rtime.info    # execution time
t1:1
t2:1
t3:1
```

## Configuration

```bash
$ cat config.linear.json
{
  "name": "linear",             # file name of the generated model file
  "output_format": "cplex_lp",  # cplex_lp/lp_solve/couenne_ampl
  "nonlinear": false,           # true/false. true: run Nemo-Aux or Nemo-Nonlinear; false: run Linear
  "relax": false,               # (works when nonlinear==True) true/false. true: Nemo-Aux, false: Nemo-Nonlinear
  "min_or_max": "min",          # min/max. Minimize or maximize the objective function
  "absolute_cria": [{           # For constraint criteria
    "is_coefficient": false,    # true/false. If false, the constraints would make all requirements to be satisfied at least once; 
                                # if false, user define the coefficients for the decision varialbes by herself.
    "crio_type": "<=",          # (works when is_coefficient==True) <, <=, =, >=, >
    "rhs": 35,                  # (works when is_coefficient==True) the number at right-hand side
    "file": "cov.info"          # coverage file (or the coefficients for the decision variables) for the constarint criterion
  }], 
  "relative_cria": [{
    "is_dependent": true,       # true/false. Models test cases nonlinearly over this criterion or not
    "weight": 1,                # weight for this criterion
    "file": "fault.info",       # coverage file for the optimization criterion
    "invert": true              # true/false. Maximize (e.g., for fault/branch coverage) or minimize (e.g., for setup effort) the criterion
  }]
}
```

## Files

* `command.txt`: the command file required by NEOS server for running Couenne
* `display.txt`: the command file required by NEOS server for running CPLEX
* `formulator.py`: the formulator of Nemo
* `generator.py`: the generator of Nemo
* `example`: the motivating example
* `subject_programs`: dataset in our evaluation, including the coverage information, faults, test cases, and source code for each subject program
* `extra_mutants.tar.gz`: extra sets of faults used in our extened evaluation for NEMO

