Resilience (socio-economic capacity) indicator for the Philippines' provinces
====================

# Contents

This repository contains several things. It will be updated regularly as the training dates approach.

## Jupyter notebooks  (*.ipynb)


* **[socio_economic_capacity](socio_economic_capacity.ipynb)** is the main demo of the model. Just click the link to see the demo. This notebook reads the socio-economic data, reads the hazard data, and runs the model.

* **[data_gathering_demo](data_gathering_demo.ipynb)** demonstrates how Python and Pandas can be used to gather data from different sources.
It is out of date and is kept only for proof-of-concept purpose.

* **[draw_maps](draw_maps.ipynb)** is the code used to draw maps from a dataset and a blank SVG map.

* **[draw_plots](draw_plots.ipynb)** demonstrates plots.

* **[policy_assessment_demo](policy_assessment_demo.ipynb)** makes systematic policy assessments and plots the result.

* **[muli_hazard_multi_period_demo](muli_hazard_multi_period_demo.ipynb)** demonstrates how to ahndle several hazard and several return periods.


## Data
All the data required to run the resilience indicator is gathered in [all_data_compiled.xlsx](all_data_compiled.xlsx).

This spreadsheet itself was compiled from diverse files Excel and csv data files in the [inputs/](inputs/) folder, using [data_gathering_demo](data_gathering_demo.ipynb).

The blank map of the Philippines' provinces is stored in [map/PHL_adm1.svg](map/PHL_adm1.svg)

## Python libraries (*.py)
The *.py files contain function definitions. Among them, res_ind_lib.py contains the main set of equations of the model. The model, and thus this file, can be modified to be tailored to the PHL context.

# Usage
Here is how to *run* these notebooks in your computer.

## Dependencies

This program **requires python3** and several libraries. The recommendation is to rely on the **Anaconda python 3 distribution**, [available for free online](https://www.continuum.io/downloads). The standard anaconda installation includes all dependencies of this program.
 Make sure you chose **python 3.x, *not* 2.x**.

**Optional dependencies** to render maps are [Inkscape](https://inkscape.org/en/) to convert SVG in PDF,  and [imagemagick](http://www.imagemagick.org/script/index.php) to convert PDF to PNG and resize images programatically. Joining all the policy assessment cards into a single pdf requires [ghostscript](http://www.ghostscript.com/download/gsdnld.html).

All requirements and optional dependencies are available for free on all plateforms. Some of them are included by default in Linux and Mac distrirbutions. To use them make sure that they are installed and accessible in the PATH of your machine. 


## Launching 
Just [download](https://github.com/adrivsh/resilience_indicator_phl/archive/master.zip) and unzip this whole folder from github. 
The run.bat program will launch the jupyter notebook for you.









