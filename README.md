# CAPyLE
CAPyLE is a cross-platform teaching tool designed and built as part of a final year computer science project. It aims to aid the teaching of cellular automata and how they can be used to model natural systems.

It is written completely in python with minimal dependencies.

![CAPyLE Screenshot on macOS](http://pjworsley.github.io/capyle/sample.png)

## Installation
The installation guide can be found on the [CAPyLE webpages](http://pjworsley.github.io/capyle/installationguide.html)

## Usage
Detailed usage can be found on the [CAPyLE webpages](http://pjworsley.github.io/capyle/).

See below for a quickstart guide:

1. `git clone https://github.com/pjworsley/capyle.git [target-directory]`
2. `cd [target-directory]`
3. Execute main.py either by:
    * `run.bat` / `run.sh`
    * `python main.py`
2. Use the menu bar to select File -> Open. This will open in the folder `./ca_descriptions`.
3. Open one of the example files;
  - `wolframs_1d.py` is Wolfram's elementary 1D automata
  - `gol_2d.py` is Conway's 2D game of life
4. The main GUI elements will now load, feel free to customise the CA parameters on the left hand panel
5. Run the CA with your parameters by clicking the bottom left button 'Apply configuration & run CA'
6. The progress bar will appear as the CA is run
7. After the CA has been run, use the playback controls at the top and the slider at the bottom to run through the simulation.
8. You may save an image of the currently displayed output using the 'Take screenshot' button

## Acknowledgements
Special thanks to [Dr Dawn Walker](http://staffwww.dcs.shef.ac.uk/people/D.Walker/) for proposing and supervising this project.

Also thanks to the COM2005 2016/2017 cohort for being the guinea-pigs!

## Licence
CAPyLE is licensed under a BSD licence, the terms of which can be found in the LICENCE file.

Copyright 2017 Peter Worsley

## Wildfire Modelling Files
For the COM3524 Group Project, we are modelling wildfires using the aforementioned CAPyLE system.

To execute the project, follow the same instructions listed above, but after running 
`python main.py`, select `main.py` within ca_descriptions.

This file contains the modelling code. Select 'Apply configuration & run CA' without manually
adjusting any of the parameters, and use the playback controls as mentioned in Usage.

Additionally, a pytest file is accessible within ca_descriptions called `testing.py`. To execute
this file, run `python -m pytest testing.py -v` in the command line from within
`./team10/ca_descriptions`. This should then execute all the tests and display which ones have
passed and failed.

The literature survey is also available to view from within the codebase. To do so, access
`./team10/literature_survey`. With a suitable TeX editor, you can then access
`literature_survey.tex` and `references.bib`. The former is the main literature survey document,
where upon opening the document, the sectioned literature survey will be visible. The latter is a BibTeX file that contains the references used within the literature survey.