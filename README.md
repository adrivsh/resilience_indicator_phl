Resilience (socio-economic capacity) indicator for the Philippines' provinces
====================

# Contents

This repository contains several things.

## Jupyter notebooks  (*.ipynb)

For training purposes, focus on the following two notebooks. (You can view them from your broswer wth no additional requirement)
* **[socio_economic_capacity_demo](socio_economic_capacity_demo.ipynb)** is the main demo of the model. (It will be updated regularly as the training dates approach). Just click here to see the demo. 
All the data used now is only for proof-of-concept purpose, and will be replaced with data provided by the PHL team.

* **[data_gathering_demo](data_gathering_demo.ipynb)** demonstrates how python can be used to gather data from different sources.

## Data
The data currently used is in the form of Excel spreadsheet, csv data files, and a shapefile of administrative boundaries in the PHL is gathered in the 'inputs/' subfolder.

## Python libraries (*.py)
The *.py files contain function definitions. Among them, res_ind_lib.py contains the main set equations of the model. The model, and thus this file, will be modified to be tailored to the PHL context.

# Usage

## Requirements

This program requires python3 and several libraries. The recommendation is to rely on the Anaconda python 3 distribution, [available for free online](https://www.continuum.io/downloads). Make sure you xhose python 3.x (not 2.x)
The standard anaconda installation includes all dependencies of this program.
Optional requirements include imagemagick and ghostscript. Maps currently rely on R, but a pure python solution is under development. All optional requirements are available online for free.

## Launching 
Just download and unzip this whole folder from github. 
The run.bat program will launch the jupyter notebook for you.









