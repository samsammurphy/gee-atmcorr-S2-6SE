## Introduction

Atmospheric correction of Sentinel 2 image collections in Google Earth Engine using a [6S emulator](https://github.com/samsammurphy/6S_emulator).

## Installation

Install [Anaconda](https://www.continuum.io/downloads).

If necessary, create a python3 environment

`conda create -n my_python3_env`

and activate it

`source activate my_python3_env`

on windows this is just

`activate my_python3_env`

then install the Earth Engine API

```
pip install google-api-python-client
pip install earthengine-api 
```

## Usage

It first time, authenticate the Earth Engine API.

`earthengine authenticate`

see the Jupyter Notebook for example usage
