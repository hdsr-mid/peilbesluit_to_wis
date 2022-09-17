[mit]: https://github.com/hdsr-mid/peilbesluitmarges/blob/main/LICENSE.txt
[marges_csv_png]: ./converter/images/wis_marges_csv.png
[marges_png]: ./converter/images/wis_marges.png

### Context
* Created: September 2022
* Authors: Renier Kramer (renier.kramer@hdsr.nl)
* Python version: >3.6

### Description
Covert a .csv to .xml to enable "operationeel peilbesluit" in FEWS WIS. Each peilgebied had 1 or more rows in 
the .csv, each row with a startdate and enddate, so that these peilmarges can vary of time. We made the following 
assumptions for validation:
- marges:
  - marges zijn altijd in cm (in csv)
  - 0cm <= eerste marge < tweede marge <= 10meter, so:
      - MIN_ALLOW_LOWER_MARGIN_CM = 0
      - MAX_ALLOW_LOWER_MARGIN_CM = 100 * 10  # yes... 10 meters
      - MIN_ALLOW_UPPER_MARGIN_CM = 0
      - MAX_ALLOW_UPPER_MARGIN_CM = 100 * 10  # yes... 10 meters
  - niet hoogwatervoorziening mag niet 0 zijn in csv (in BR, maar in Inger's FME script niet)
  - peilgebied waar geen marges zijn worden gefixed (weggelaten/ingevuld) in Inger's FME script
  - marges moeten te converteren zijn naar floats
  - marges moeten altijd ingevuld zijn (regels zonder marge fixen (bijv weglaten) in Inger's FME script)
- peilen:
   - toegestane peilen domein: -10mNAP tm 10mNAP
   - peilen zijn altijd in mnap
   - peilen moeten te converteren naar floats
   - peilen moeten altijd ingevuld zijn (fix nodig (bijv weglaten) in Inger's FME script
- datums:
  - 1 peilgebied kan >1 csv regels hebben, met elk een eigen start- en einddatum. In geval van >1 regels:
    - regels moeten chronologisch gesorteerd zijn 
    - geen geen gat/overlap tussen regels
- foutafhandeling:
   - als 1 csv regel van een peilgebied foutief is, dan worden alle regels van die dat peilgebied niet meegenomen


After validation of the .csv we convert this (yellow rows): 
![marges_csv_png]
to this (straight lines):
![marges_png]


### Usage
1. build conda environment from file if you don't have environment already
```
> conda env create --name peilbesluitmarges --file <path_to_project>/environment.yml
```
2. Define all constants in peilbesluitmarges/converter/constants.py
   - set CREATE_CSV_WITH_ERRORS=False to create the validation result of the .csv 
   - set CREATE_XML=True to create the .xml that goes into FEWS  
3. run project:
```
> conda activate peilbesluitmarges
> python <path_to_project>/main.py
```

### License 
[MIT][mit]



### Releases
None

### Contributions
All contributions, bug reports, bug fixes, documentation improvements, enhancements and ideas are
welcome on https://github.com/hdsr-mid/peilbesluitmarges/issues


### Test Coverage
no test exists yet...


### Conda general tips
#### Build conda environment (on Windows) from any directory using environment.yml:
Note1: prefix is not set in the environment.yml as then conda does not handle it very well
Note2: env_directory can be anywhere, it does not have to be in your code project
```
> conda env create --prefix <env_directory><env_name> --file <path_to_project>/environment.yml
# example: conda env create --prefix C:/Users/xxx/.conda/envs/project_xx --file C:/Users/code_projects/xx/environment.yml
> conda info --envs  # verify that <env_name> (project_xx) is in this list 
```
#### Start the application from any directory:
```
> conda activate <env_name>
At any location:
> (<env_name>) python <path_to_project>/main.py
```
#### Test the application:
```
> conda activate <env_name>
> cd <path_to_project>
> pytest  # make sure pytest is installed (conda install pytest)
```
#### List all conda environments on your machine:
```
At any location:
> conda info --envs
```
#### Delete a conda environment:
```
Get directory where environment is located 
> conda info --envs
Remove the enviroment
> conda env remove --name <env_name>
Finally, remove the left-over directory by hand
```
#### Write dependencies to environment.yml:
The goal is to keep the .yml as short as possible (not include sub-dependencies), yet make the environment 
reproducible. Why? If you do 'conda install matplotlib' you also install sub-dependencies like pyqt, qt 
icu, and sip. You should not include these sub-dependencies in your .yml as:
- including sub-dependencies result in an unnecessary strict environment (difficult to solve when conflicting)
- sub-dependencies will be installed when dependencies are being installed
```
> conda activate <conda_env_name>

Recommended:
> conda env export --from-history --no-builds | findstr -v "prefix" > --file <path_to_project>/environment_new.yml   

Alternative:
> conda env export --no-builds | findstr -v "prefix" > --file <path_to_project>/environment_new.yml 

--from-history: 
    Only include packages that you have explicitly asked for, as opposed to including every package in the 
    environment. This flag works regardless how you created the environment (through CMD or Anaconda Navigator).
--no-builds:
    By default, the YAML includes platform-specific build constraints. If you transfer across platforms (e.g. 
    win32 to 64) omit the build info with '--no-builds'.
```
#### Pip and Conda:
If a package is not available on all conda channels, but available as pip package, one can install pip as a dependency.
Note that mixing packages from conda and pip is always a potential problem: conda calls pip, but pip does not know 
how to satisfy missing dependencies with packages from Anaconda repositories. 
```
> conda activate <env_name>
> conda install pip
> pip install <pip_package>
```
The environment.yml might look like:
```
channels:
  - defaults
dependencies:
  - <a conda package>=<version>
  - pip
  - pip:
    - <a pip package>==<version>
```
You can also write a requirements.txt file:
```
> pip list --format=freeze > <path_to_project>/requirements.txt
```
