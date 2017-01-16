# Mesoscale-Brain-Explorer (MBE)

## Installation
Windows users simply have to download and extract the most recent 
release and run pipegui.exe contained within
The most recent version can be downloaded [here](https://github.com/Frikster/Mesoscale-Brain-Explorer/releases/tag/0.5.1)

Linux users will need Python 3.5 64-bit and the following dependencies 
installed:
```bash
pip3.5 install pandas scipy matplotlib tifffile psutil imreg_dft
pip3.5 install pyqtgraph
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install python3-pyqt4 python3-pyqt4.qtopengl build-essential libgtk2.0-dev libjpeg-dev libtiff4-dev libjasper-dev libopenexr-dev cmake python-dev python-numpy python-tk libtbb-dev libeigen3-dev yasm libfaac-dev libopencore-amrnb-dev libopencore-amrwb-dev libtheora-dev libvorbis-dev libxvidcore-dev libx264-dev libqt4-dev libqt4-opengl-dev sphinx-common texlive-latex-extra libv4l-dev libdc1394-22-dev libavcodec-dev libavformat-dev libswscale-dev default-jdk ant libvtk5-qt4-dev
```

Please download and install the latest pyqtgraph package from the 
following link if it fails via the terminal: http://www.pyqtgraph.org/

Clone this repo or download as a zip
Now open the terminal at *Mesoscale-Brain-Explorer/src* and execute the 
following to run MBE
```bash
python3.5 pipegui.py
```

## User Manual
### Overview Tutorial
The following [tutorial series](https://www.youtube.com/playlist?list=PLlnQ3H3mPPQROgoe-t3Hrhv4zdiJyw5Gs) steps through setting up the application in Windows as well how to easily replicate all figures in our paper (seed pixel correlation maps, connectivity matrix, activity plots)

### Seed/ROI Placement csv/txt format
For the Seed/ROI Placement plugins a specific format is *required* for your coordinates to see proper importation into your MBE project. Here is an example from an Ai mouse's coordinates in microns.  Coordinates were adapted from the [Allen Mouse Brain Connectivity Atlas](http://connectivity.brain-map.org/). We previously [mapped functional and anatomical coordinates of transgenic mice using sensory stimulation](https://www.ncbi.nlm.nih.gov/pubmed/22435052) in combination with in vivo large-scale cortical mapping using Channelrhodopsin-2 stimulation to confirm the coordinates.

| 1) ROI Name   | 2) Length     | 3) X Coordinate  | 4) Y Coordinate |
| ------------- | ------------- | ---------------- | ----------------|
| L-V1          | 1             | -2500.0          |  -2500.0        |
| L-BC          | 1             | -3500.0          |  -1000.0        |
| L-HL          | 1             | -2000.0          |     -0.0        |
| L-M1          | 1             | -1500.0          |   1750.0        |
| L-M2          | 1             | -1000.0          |   2500.0        |
| L-RS          | 1             | -500.0           |  -2500.0        |
| L-AC          | 1             | -500.0           |      0.0        |
| R-V1          | 1             |  2500.0          |  -2500.0        |
| R-BC          | 1             |  3500.0          |  -1000.0        |
| R-HL          | 1             |  2000.0          |     -0.0        |
| R-M1          | 1             |  1500.0          |   1750.0        |
| R-M2          | 1             |  1000.0          |   2500.0        |
| R-RS          | 1             |  500.0           |  -2500.0        |
| R-AC          | 1             |  500.0           |      0.0        |

For your coordinates, there *must* be 4 columns if you are importing for the ROI Placement plugin. Otherwise, there *must* be 3 with the length column omitted for the Seed Placement plugin (Seeds have length 1). Next, for the column names the "1)" *must* exist for the column with ROI names, a "2)" for the length column, a "3)" for X Coordinates and "4)" for the Y Coordinate. For seeds omit the length column. Thus "2)" for X Coordinate and "3)" for Y Coordinate columns. Your coordinates can be named whatever you please. 

## For Developers
If you are developing on Ubuntu simply follow the installation 
instructions and then use your favourite IDE to modify the code

Windows users will need Python 3.5 64-bit. Clone 
this repo or download as a zip, open the terminal at
 *Mesoscale-Brain-Explorer/whl* and execute the 
following to install all dependencies

Please download:
* [numpy-x.x.x+mkl-cp35-cp35m-win_amd64.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy)
* [PyQt4-x.x.x-cp35-none-win_amd64.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyqt4)
* [pandas-x.x.x-cp35-cp35m-win_amd64.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pandas)
* [matplotlib-x.x.x-cp35-cp35m-win_amd64.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib)
* [scipy-x.x.x-cp35-cp35m-win_amd64.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/#scipy)
* [tifffile-x.x.x-cp35-cp35m-win_amd64.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs)
* [psutil-x.x.x-cp35-cp35m-win_amd64.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/#psutil)
* [pyqtgraph-x.x.x-py2.py3-none-any.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/)
* [imreg_dft-x.x.x-py2.py3-none-any.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/)
* [PyOpenGL-x.x.x-cp35-cp35m-win_amd64.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyopengl)
* [opencv_python-x.x.x-cp35-cp35m-win_amd64.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/#opencv)

x.x.x in each case simply means the latest version

Go to the folder where all .whl files are downloaded and run:
```bash
pip3.5 install "numpy-1.11.2+mkl-cp35-cp35m-win_amd64.whl" PyQt4-4.11.4-cp35-none-win_amd64.whl pandas-0.19.1-cp35-cp35m-win_amd64.whl matplotlib-2.0.0b4-cp35-cp35m-win_amd64.whl scipy-0.18.1-cp35-cp35m-win_amd64.whl tifffile-2016.10.28-cp35-cp35m-win_amd64.whl psutil-5.0.0-cp35-cp35m-win_amd64.whl pyqtgraph-0.10.0-py2.py3-none-any.whl imreg_dft-2.0.0-py2.py3-none-any.whl PyOpenGL-3.1.1-cp35-cp35m-win_amd64.whl opencv_python-3.1.0-cp35-cp35m-win_amd64.whl
```
This may take a while to complete. 
Once done, use your favourite IDE to modify the code

### Custom Plugin Tutorial
Coming soon... (with pictures and videos)
