# Mesoscale-Brain-Explorer (MBE)

## Installation

Windows users simply have to download and extract the most recent release and run pipegui.exe contained within

Linux users will need Python 3.5 and the following dependencies installed:
> sudo apt-get update
> sudo apt-get upgrade
> pip3 install pandas scipy matplotlib tifffile psutil imreg_dft parmap
> pip3 install pyqtgraph
> sudo apt-get install python3-pyqt4 python3-pyqt4.qtopengl build-essential libgtk2.0-dev libjpeg-dev libtiff4-dev libjasper-dev libopenexr-dev cmake python-dev python-numpy python-tk libtbb-dev libeigen3-dev yasm libfaac-dev libopencore-amrnb-dev libopencore-amrwb-dev libtheora-dev libvorbis-dev libxvidcore-dev libx264-dev libqt4-dev libqt4-opengl-dev sphinx-common texlive-latex-extra libv4l-dev libdc1394-22-dev libavcodec-dev libavformat-dev libswscale-dev default-jdk ant libvtk5-qt4-dev

Please download and install the latest pyqtgraph package from the following link if it fails via the terminal: http://www.pyqtgraph.org/

Now open the terminal at *Mesoscale-Brain-Explorer/src* and execute the following to run MBE
> python3 pipegui.py