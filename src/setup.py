#!/usr/bin/env python3
from cx_Freeze import setup, Executable

exe=Executable(
     script="pipegui.py",
     base="Win32Gui",
     icon="Icon.ico"
     )
includefiles=[]
includes=[]
excludes=[]
packages=[]
setup(

     version = "0.2.0",
     description = "No Description",
     author = "Cornelis Dirk Haupt",
     name = "Mesoscale Brain Explorer",
     options = {'build_exe': {'excludes':excludes,'packages':packages,'include_files':includefiles}},
     executables = [exe]
     )