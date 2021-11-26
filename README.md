# Pyswip-Notebook
 
This package makes the python-prolog-bridge [pyswip](https://github.com/yuce/pyswip) useable from within a jupyter notebook environment.
For each instance of the new `IsolatedProlog`-class will spawn it's own prolog-module (like a namespace) and multiple instances (also when a cell is executed multiple times)
will be isolated from one another. 


## Installation

### Dependencies

Follow the installation instructions for pyswip [here](https://github.com/yuce/pyswip/blob/master/INSTALL.md) to 
install a prolog interpreter for your operating system.

### Using pip
```
pip install pyswip-notebook
```

### From source
```
git clone https://github.com/mortacious/pyswip-notebook.git
cd pyswip-notebook
python setup.py install
```

## Usage

See `examples/example.ipynb` for usage examples.