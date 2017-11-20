# Mesoscale-Brain-Explorer (MBE)
Please cite [this](http://dx.doi.org/10.1117/1.NPh.4.3.031210) article if you find this application or its code useful.

## Warnings and Notes
* a "ret_files" or "OSError: <-number-> requested and 0 written" typically means you have run out of space on your hard drive. MBE uses up hard disk space fast if you are processing large files since it saves all intermediate steps to file.
* The application will often appear to be unresponsive (i.e. you'll see the words "not responding.") This occurs often and does not mean the application is broken. It typically always means the application is busy working. Wait for the progress bar to complete.
* MBE is written in python to make it easy to modify, but at the expense of increasing memory load. We recommend you have at least 4 times as much RAM as the largest file you wish to process. e.g. if the largest file you wish to process through the application is 2GB please ensure you have at least 8GB RAM.
* Aborting a process has still not been fully implemented (it is in-progress). You will not be able to stop a processing step you have started other than force closing. 

## Installation
The application has been tested and appears to work on Windows 7,8.1,10 and Ubuntu 16.04.2

### Windows
Windows users simply have to download and extract the most recent 
release and run the .exe contained within the pipegui folder.
The most recent version can be downloaded [here](https://github.com/Frikster/Mesoscale-Brain-Explorer/releases)

#### Visual C++ Redistributable 
The application does not seem to work with earlier (e.g. 2008) versions of Visual C++ Redistributable. If you do not have Visual Studio 2017, follow these instructions to upgrade:

1. Install Windows Updates:
  * Go to Start - Control Panel - Windows Update
  * Check for updates
  * Install all available updates.
  * After the updates are installed, restart your computer.
  * After the restart repeat the steps above again until no more updates are available.
2. Download the Visual C++ Redistributable:
  * For Windows 64-bit
[Visual C++ Redistributable for Visual Studio 2017 (64-bit)](http://download.microsoft.com/download/9/3/F/93FCF1E7-E6A4-478B-96E7-D4B285925B00/vc_redist.x64.exe)
  * For Windows 32-bit
[Visual C++ Redistributable for Visual Studio 2017 (32-bit)](http://download.microsoft.com/download/9/3/F/93FCF1E7-E6A4-478B-96E7-D4B285925B00/vc_redist.x86.exe)
3. Run the vcredist_x64.exe (64-bit) or vcredist_x86.exe (32-bit) and select Uninstall
4. Run the .exe again and select Install

### Linux
Linux users will need Python 3.5 64-bit and the following dependencies 
installed (This instruction set was last tested **March 2017 on Ubuntu 16.04.2** by running each line by line):
```bash
sudo pip3 install pandas scipy matplotlib tifffile psutil imreg_dft
sudo pip3 install pyqtgraph
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install python3-pyqt4 python3-pyqt4.qtopengl build-essential libgtk2.0-dev libjpeg-dev libtiff5-dev libjasper-dev libopenexr-dev cmake python-dev python-numpy python-tk libtbb-dev libeigen3-dev yasm libfaac-dev libopencore-amrnb-dev libopencore-amrwb-dev libtheora-dev libvorbis-dev libxvidcore-dev libx264-dev libqt4-dev libqt4-opengl-dev sphinx-common texlive-latex-extra libv4l-dev libdc1394-22-dev libavcodec-dev libavformat-dev libswscale-dev default-jdk ant libvtk5-qt4-dev
sudo pip3 install opencv-python
sudo pip3 install pyopengl
```

The above intructions assume you have pip3 set up. If you don't simply do this:
```bash
sudo apt-get update
sudo apt-get -y install python3-pip
pip3 install --upgrade pip
```

openCV can be tricky to install. Try [this tutorial](https://www.begueradj.com/installing-opencv-3.2.0-for-python-3.5.2-on-ubuntu-16.04.2-lts.html) if ```bash pip3 install opencv-python``` fails. Please download and install the latest pyqtgraph package from the following link if it fails via the terminal: http://www.pyqtgraph.org/

Clone this repo or download as a zip

Now open the terminal at *Mesoscale-Brain-Explorer/src* and execute the 
following to run MBE
```bash
python3.5 pipegui.py
```
#### Note to Ubuntu users
* Exporting to .avi does not work on Ubuntu but it does on Windows. You can still export to .tiff or .raw on Ubuntu and all other functions seem to work
* The connectivity matrix labels UI labels are missing in Ubuntu (but not in Windows). This does not affect functionality and exporting it to a csv still reveals which ROI each cell belongs to. You can still tell what order the Matrix is in my referring to the order you assigned them in the ROI list (they can be rearranged)

## User Manual
### Overview Tutorial
The following [tutorial series](https://www.youtube.com/watch?v=v-owB1WEwSE&list=PLypXUmdWxFUQHg2Y0rQkTcmf1GHHhcc0K) steps through setting up the application in Windows as well how to easily replicate all figures in our paper (seed pixel correlation maps, connectivity matrix, activity plots).

### Sample Data
Example image stacks from mouse #0285 used in the manuscript can be downloaded [here](https://drive.google.com/open?id=0B3eRv-4znU32SGQ3V2ZVa21EWUE). These can be used along with the tutorial.

### Seed/ROI Placement csv/txt format
The ROI Import plugin a specific format is *required* for your coordinates to see proper importation into your MBE project. Here is an example from an Ai mouse's coordinates in microns.  Coordinates were adapted from the [Allen Mouse Brain Connectivity Atlas](http://connectivity.brain-map.org/). We previously [mapped functional and anatomical coordinates of transgenic mice using sensory stimulation](https://www.ncbi.nlm.nih.gov/pubmed/22435052) in combination with in vivo large-scale cortical mapping using Channelrhodopsin-2 stimulation to confirm the coordinates.

| 1) ROI Name   | 2) Length     | 3) X Coord (ML)  | 4) Y Coord (AP) |
| ------------- | ------------- | ---------------- | ----------------|
| L-A          | 1             | -2293.2           |  -2496.2        |
| L-AC          | 1             | -260             |  270            |
| L-AL          | 1             | -3827.1          |  -3339.3        |
| L-AM          | 1             | -1647.9          |   -2696        |
| L-AU          | 1             | -4530.4          |   -2901        |
| L-BC          | 1             | -3456.9           |  -1727        |
| L-FL          | 1             | -2452.6           |  -566.8        |
| L-HL          | 1             |  -1694.2          |  -1145.7        |
| L-L          | 1             |  -3712.6          |  -4261.5        |
| L-LI          | 1             |  -4058.6          |  -4229.3        |
| L-M1          | 1             |  -1860.3          |   641.81        |
| L-M2          | 1             |  -870.02          |   1420.5        |
| L-MO          | 1             |  -3491.7           |  587.12        |
| L-NO          | 1             |  -3800.1           |   -477.33     |
| L-PL          | 1             | -3516.1          |  -5214.6        |
| L-PM          | 1             | -1621.7          |  -3624.7        |
| L-POR          | 1             | -4223.1          |     -4755      |
| L-RL          | 1             | -3171.2          |   -2849        |
| L-RS          | 1             |  -620.43          |   -2885.8        |
| L-S2          | 1             | -4397.7           |  -1202.7        |
| L-TEA          | 1             | -4565.7           |   -4162.2        |
| L-TR          | 1             |  -1864.4          |  -2020.4        |
| L-UN          | 1             |  -2797.9          |  -971.12        |
| L-V1          | 1             |  -2516.8          |   -4267.8        |
| R-A          | 1             |  2293.2          |  -2496.2        |
| R-AC          | 1             |  260             |  270           |
| R-AL          | 1             |  3827.1          |  -3339.3        |
| R-AM          | 1             | 1647.9          |   -2696        |
| R-AU          | 1             | 4530.4          |   -2901        |
| R-BC          | 1             | 3456.9           |  -1727        |
| R-FL          | 1             | 2452.6           |  -566.8        |
| R-HL          | 1             |  1694.2          |  -1145.7        |
| R-L          | 1             |  3712.6          |  -4261.5        |
| R-LI          | 1             |  4058.6          |  -4229.3        |
| R-M1          | 1             |  1860.3          |   641.81        |
| R-M2          | 1             |  870.02          |   1420.5        |
| R-MO          | 1             |  3491.7           |  587.12        |
| R-NO          | 1             |  3800.1           |   -477.33     |
| R-PL          | 1             | 3516.1          |  -5214.6        |
| R-PM          | 1             | 1621.7          |  -3624.7        |
| R-POR          | 1             | 4223.1          |     -4755      |
| R-RL          | 1             | 3171.2          |   -2849        |
| R-RS          | 1             |  620.43          |   -2885.8        |
| R-S2          | 1             | 4397.7           |  -1202.7        |
| R-TEA          | 1             | 4565.7           |   -4162.2        |
| R-TR          | 1             |  1864.4          |  -2020.4        |
| R-UN          | 1             |  2797.9          |  -971.12        |
| R-V1          | 1             |  2516.8          |   -4267.8        |


For your coordinates, there *must* be 4 columns. Next, for the column names the "1)" *must* exist for the column with ROI names, a "2)" for the length column, a "3)" for X Coordinates and "4)" for the Y Coordinate. Your coordinates can be named whatever you please. 

Note that if coordinates are being used as seeds for seed pixel correlation (SPC) mapping that the length column is still required for import, however will not be used by the SPC plugin as all seeds have a length of 1 pixel.

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

Note that you may get the following error: `ImportError: DLL load failed: The specified procedure could not be found.` If you do download https://github.com/Frikster/Mesoscale-Brain-Explorer/blob/master/msvcp140.dll and place it in the same site-package folder that contains QtCore4.dll. This is usually C:\Python35\Lib\site-packages\PyQt4\ if you installed Python to C:\Python35.

### Custom Plugin Tutorial
See the following [Google doc](https://docs.google.com/document/d/1T7hzB444M9UHi4l09OjLi4QMDtZwMx3ZYqIHAUGiBEc/edit?usp=sharing).
