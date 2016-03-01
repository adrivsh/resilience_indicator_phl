Resilience (socio-economic capacity) indicator for the Philippines' provinces
====================

# Contents

This repository contains several things. (It will be updated regularly as the training dates approach).

## Jupyter notebooks  (*.ipynb)

For training purposes, focus on the following two notebooks. (You can view them from your broswer with no additional requirement)
* **[socio_economic_capacity_demo](socio_economic_capacity_demo.ipynb)** is the main demo of the model. Just click the link to see the demo. 

* **[data_gathering_demo](data_gathering_demo.ipynb)** demonstrates how Python and Pandas can be used to gather data from different sources.
All the data used now is only for proof-of-concept purpose, and can be replaced with data provided by the Philippine government.

## Data
All the data required to run the resilience indicator is gathered in [all_data_compiled.xlsx](all_data_compiled.xlsx).

Thi spreadsheet itself was compiled from diverse files Excel and csv data files in the [inputs/](inputs/) folder, using [data_gathering_demo](data_gathering_demo.ipynb).

## Python libraries (*.py)
The *.py files contain function definitions. Among them, res_ind_lib.py contains the main set of equations of the model. The model, and thus this file, can be modified to be tailored to the PHL context.

# Usage

## Dependencies

This program **requires python3** and several libraries. The recommendation is to rely on the **Anaconda python 3 distribution**, [available for free online](https://www.continuum.io/downloads). The standard anaconda installation includes all dependencies of this program.
 Make sure you chose **python 3.x, *not* 2.x**.

**Optional dependencies** to render maps are [Inkscape](https://inkscape.org/en/) to convert SVG in PDF,  and [imagemagick](http://www.imagemagick.org/script/index.php) to convert PDF to PNG and resize images programatically. Rendering provincial cards may additionally require pdfcrop and ghostscript.

All requirements and optional dependencies are available for free on all plateforms. Some of them are included by default in Linux and Mac distrirbutions. To use them make sure that they are installed and accessible in the PATH of your machine. 


## Launching 
Just download and unzip this whole folder from github. 
The run.bat program will launch the jupyter notebook for you.









