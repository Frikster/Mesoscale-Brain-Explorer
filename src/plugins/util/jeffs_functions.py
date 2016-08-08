import os
import glob

def check_mice(the_dir):
    os.chdir(the_dir)
    the_file_list=glob.glob('*.*')
    mouse_list=[]
    for f in the_file_list:
        if not (f[1:11] in mouse_list):
            mouse_list.append(f[1:11])
    return mouse_list

def check_cages(base_path_data):
    cage_dirs=next(os.walk(base_path_data))[1]
    return cage_dirs


def check_dirs(base_path_data,base_path_analysis):
    #this one is where we have the data from the pi somewhere on the network.
    #base_path_data='/Users/jledue/Documents/PYTHON/AHF Data/'

    data_dirs=next(os.walk(base_path_data))[1]
    analysis_dirs=next(os.walk(base_path_analysis))[1]

    to_analyze=[]
    for d in data_dirs:
        if d in analysis_dirs:
           print('we did this one: '+d)
        else:
           print('we must analyze this one: '+d)
           to_analyze.append(d)
    return to_analyze

#test=check_dirs('/Users/jledue/Documents/PYTHON/AHF Data/','/Users/jledue/Documents/PYTHON/AHF Analysis/')
#print(test)
#test=check_cages('/Users/jledue/Documents/PYTHON/AHF Data/0809/')
#print(test)
#test=check_mice('/Users/jledue/Documents/PYTHON/0809 files/Videos1')
#print(test)