[mit]: https://github.com/hdsr-mid/peilbesluitmarges/blob/main/LICENSE.txt
[marges_csv_png]: ./converter/images/wis_marges_csv.png
[marges_png]: ./converter/images/wis_marges.png

### Context
* Created: September 2022
* Authors: Renier Kramer (renier.kramer@hdsr.nl)
* Python version: 3.7

### Description
Validate and covert a .csv to .xml to enable "operationeel peilbesluit" in FEWS WIS. Each peilgebied in the .csv 
has >=1 rows in the .csv, and each row has a start- and enddate and peilmarges. 
Thus, these peilmarges can vary over time (see 'Validation assumptions' below). 

### Development
This codebase is a mesh and contains a lot of complexity that would have not been there if I used more deps.
Why? At the start of the project, we (Roger, Job and I) decided this code would run in FEWS itself. Therefore, I used
as little deps. For example, I used python built-in 'csv' instead of deb 'pandas'. 
However, at the end of this project, we decided to run this code outside FEWS. I managed to replace most of the 
'csv-instead-of-pandas' complexity, but a lot of the original code structure still exists.  

### Workflow

##### Things to do on beforehand:
- Ask team 'Peilbesluiten' (see input below) to create a new PEILMARGE_GIS_EXPORT .csv file.

##### Input:
- One .csv with peilmarges that is exported from ArcGis with an FME script.
  - It exports to PEILMARGE_GIS_EXPORT_FILE_PATH (see in converter/constants.py)
  - The FEM script is developed and maintained by team 'GIS' (Inger) 
  - This export is not scheduled, but carried out on demand by team 'Peilbesluiten' (Hielke)

##### Output:
- One data/output/{datetime}/orig.csv
- One data/output/{datetime}/orig_with_errors.csv
- One data/output/{datetime}/without_errors_that_will_be_used_for_FEWS_WIS_xml.csv
- Optionally, one data/output/{datetime}/PeilbesluitPi.xml dependent on CREATE_XML (bool) in converter/constants.py


### Usage
1. Make sure you have Anaconda installed. Verify by: Windows key -> 'Anaconda Prompt 3 (Prod)'. Note that you can not use cmd as:
   - it may result in a 'CondaHttpError' when building conda environment (step 2b).
   - Moreover, within VDI you can do 'conda info --envs' but not 'conda activate <env_name>'...

2. Run this in Anaconda Prompt 3 (Prod):
    - (2a): go to the O: drive
      ```
      O:
      ```
    - (2b): change directory (cd) to the root of this code project 
      ```
      cd Planvorming/GIS/Peilbesluiten/Aanpak Actuele Peilbesluiten/git/peilbesluitmarges_copy
      ```
3. Prepare Check if you have the conda environment:
    - (3a): get the list with existing conda environments
      ```
      conda info --envs
      ```
    - (3b): if 'peilbesluitmarges' is listed, go to step (4a)
    - (3c): build the conda environment (this takes an hour!!) and needs to be done only 1 time  
      ```
      conda env create --name peilbesluitmarges --file environment.yml
      ```
    - (3d): verify if 3d is success with step (3a)
      
4. Point app to the correct input file
   - (4a): open in 'Windows verkenner' file ./peilbesluitmarges_copy/converter/constants.py
   - (4b): update PEILMARGE_GIS_EXPORT_FILE_PATH to the file you want
    
5. Run project:
   - (5a): activate the conda environment
     ```
     conda activate peilbesluitmarges
     ```
   - (5b): run the python project
     ``` 
     python main.py
     ```

6. See output by opening 'Windows verkenner' directory ./peilbesluitmarges_copy/converter/data/output/


### Validation assumptions
We made the following assumptions for validation:
- marges:
  - marges zijn altijd in cm (in csv)
  - 0cm <= eerste marge <= tweede marge <= 10meter, so:
      - MIN_ALLOW_LOWER_MARGIN_CM = 0
      - MAX_ALLOW_LOWER_MARGIN_CM = 100 * 10  # yes... 10 meters
      - MIN_ALLOW_UPPER_MARGIN_CM = 0
      - MAX_ALLOW_UPPER_MARGIN_CM = 100 * 10  # yes... 10 meters
  - een niet-hoogwatervoorziening mag niet marge = 0 hebben in .csv (in BR wel, maar in Inger's FME script niet)
  - peilgebied zonder marges worden gefixed (weggelaten/ingevuld) in Inger's FME script
  - marges moeten te converteren zijn naar floats
  - marges moeten altijd ingevuld zijn (regels zonder marge fixen (bijv weglaten) in Inger's FME script)
- peilen:
   - toegestane peilen domein: -10mNAP tm 10mNAP
   - peilen zijn altijd in mNAP
   - peilen moeten te converteren naar floats
   - peilen moeten altijd ingevuld zijn (fix nodig (bijv weglaten) in Inger's FME script
- datums:
  - 1 peilgebied kan >1 csv regels hebben, met elk een eigen start- en einddatum. In geval van >1 regels:
    - geen geen gat/overlap tussen regels
    - datum format is YYYY-MM-DD
- foutafhandeling:
   - als 1 csv regel van een peilgebied foutief is, dan worden alle regels van die dat peilgebied niet meegenomen

After validation of the .csv we convert this (yellow rows): 
![marges_csv_png]
to this (straight lines):
![marges_png]


### License 
[MIT][mit]

### Releases
None

### Contributions
All contributions, bug reports, bug fixes, documentation improvements, enhancements and ideas are
welcome on https://github.com/hdsr-mid/peilbesluitmarges/issues


### Test Coverage
```
---------- coverage: platform win32, python 3.7.12-final-0 -----------
Name                              Stmts   Miss  Cover
-----------------------------------------------------
converter\constants.py              106      5    95%
converter\convert.py                210     50    76%
converter\timeseries_builder.py     126      8    94%
converter\utils.py                   26      6    77%
converter\xml_builder.py            134      5    96%
main.py                              36     36     0%
-----------------------------------------------------
TOTAL                               638    110    83%
```

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
