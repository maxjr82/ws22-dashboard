# WS22 database: towards configurationally diverse molecular datasets

![python version](https://img.shields.io/badge/python-3.8-blue?logo=python) 
![Streamlit](https://img.shields.io/badge/Streamlit-Library-orange.svg)

This repository contains a dashboard application developed with Streamlit to facilitate the preliminary
data exploration of the molecular datasets available in the WS22 database hosted in the ZENODO repository
(https://doi.org/10.5281/zenodo.7032333). The dashboard provides an interactive framework for the users
to easily navigate through the data by visualizing the molecular conformations and anticipating statistical 
insights via histograms and boxplots of the quantum chemical properties and geometrical features stored in
the datasets.

## Requirements

The dashboard was designed to work with Python3 (tested with version 3.8.1). In addition to the Streamlit
application, one needs to install the following Python packages:

- ase (Atomic Simulation Environment)
- numpy
- pandas
- plotly
- py3Dmol
- requests

## How to use

To run the dashboard locally, one needs first to download the application from this GitHub repository, and
then run the provided Python script directly from a Linux terminal as follows:

```sh
$ streamlit run app/dashboard.py
```

It is not necessary to download the datasets to the local machine to run the application. The data will be 
read directly from the ZENODO repository.
