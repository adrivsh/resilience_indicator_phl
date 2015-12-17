Resilience (socio-economic capacity) indicator for the Philippines' provinces
====================

# Contents

This repository contains several things.

## Python libraries (*.py)
The *.py files contain function definitions. Among them, res_ind_lib.py contains the main set equations of the model. The model, and thus this file, will be modified to be tailored to the PHL context.

## Jupyter notebooks  (*.ipynb)
* compute_res_ind is the main one. It demonstrates how to gather data from different sources in python, and runs the resilience indicator with this data.
This notebook also runs a sensitivity analysis that can be used to check the robustness of the results, as well as to run what-if policy scenario analysis.
All the data used now is only for proof-of-concept purpose, and will be replaced with data provided by the PHL team.

* compute_scorecard is the notebook used to compute the derivatives of the model. This information is needed to draw the scorecards

* render_scorecards is used to actually draw the scorecards, and build the pdf containing all the scorecards. The design of the scorecards will be updated to meet the PHL needs.

* eps_to_png can be used to convert the scorecards to images

* draw_maps_and_plots demonstrates how to draw maps with the results, as well as rudimentary plots. This will be updated to provide the illustrations that the PHL team need.

## Data
The data currently used is in the form of Excel spreadsheet, csv data files, and a shapefile of administrative boundaries in the PHL is gathered in the 'inputs/' subfolder.

# Usage

## Requirements

This program requires python3 and several libraries. The recommendation is to rely on the Anaconda python distribution, available for free online. The standard anaconda installation includes all dependencies of this program.

Optional requirements include imagemagick and ghostscript. Maps currently rely on R, but a pure python solution is under development. All optional requirements are available online for free.

## Launching 
Just download and unzip this whole folder from github. The run.bat program will launch the jupyter notebook for you.









