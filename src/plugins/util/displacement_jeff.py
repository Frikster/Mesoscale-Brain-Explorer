from filter_jeff import load_frames, filter2_test_j
from math import pow, sqrt
import os
import numpy as np
import matplotlib.pyplot as plt
import parmap
import image_registration

'''
base_dir = ["/Volumes/My Passport/DataFB_Backup/AutoHeadFix_Data/0730/EL_LRL_fluc/",
"/Volumes/My Passport/DataFB_Backup/AutoHeadFix_Data/0730/EL_LRL_fluc/",
"/Volumes/My Passport/DataFB_Backup/AutoHeadFix_Data/0730/EL_LRL_fluc/",
"/Volumes/My Passport/DataFB_Backup/AutoHeadFix_Data/0730/EL_LRL_fluc/",
"/Volumes/My Passport/DataFB_Backup/AutoHeadFix_Data/0730/EL_LRL_fluc/"
]

mice = ["1312000377", "2015050115", "1302000245", "1312000159", "1312000300"]
#mice = ["1312000377"]



#mice = ["1312000377", "2015050115", "1302000245", "1312000159", "1312000300", "2015050202", "1312000573"]
frame_oi = 400
limit_time = 1438365391.603202
'''

class Position:
    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy
        self.dd = sqrt(pow(dx, 2) + pow(dy, 2))

def get_file_list(base_dir, mouse):
    print(base_dir)
    lof = []
    lofilenames = []
    for root, dirs, files in os.walk(base_dir):
            for file in files:
                if (file.endswith(".raw") or file.endswith(".g") ) and mouse in file:
                    #print os.path.join(root, file)
                    #if check_time_is_valid(file):
                    #    lof.append((os.path.join(root, file)))
                    #    lofilenames.append(file)
                    #else:
                    #    print file
                    lof.append((os.path.join(root, file)))
                    lofilenames.append(file)
    return lof, lofilenames


def check_time_is_valid(video_file):
    time = video_file[12:-4]
    if float(time) <= limit_time:
        return False
    else:
        return True

def get_video_frames(lof,width,height):
    list_of_trial_frames = []
    for video_file in lof:
        print("Getting frames: " + video_file)
        frames = get_frames(video_file,width,height)
        frames = frames[:800, :, :]
        print(np.shape(frames))
        list_of_trial_frames.append(frames)
    print(np.shape(list_of_trial_frames))
    return list_of_trial_frames

def get_green_video_frames(lof,width,height):
    print('')
    print('in get_green_video_frames')
    print(lof)
    list_of_trial_frames = []
    lof_tmp=[]
    lof_tmp.append(lof)
    print((type(lof_tmp)))
    for video_file in lof_tmp:
        print(("Getting green frames: " + str(video_file)))
        frames = get_green_frames(video_file,width,height)
        frames = frames[:800, :, :]
        print(np.shape(frames))
        list_of_trial_frames.append(frames)
    print(np.shape(list_of_trial_frames))
    return list_of_trial_frames

def get_all_processed_frames(lof):
    list_of_trial_frames = []
    for video_file in lof:
        print("Getting frames: " + video_file)
        frames = get_processed_frames(video_file)
        print(np.shape(frames))
        list_of_trial_frames.append(frames)
    print(np.shape(list_of_trial_frames))
    return list_of_trial_frames

def find_min_ref(lor):
    curr_min = 100
    print(np.shape(lor))
    for positions in lor:
        sum = 0
        for position in positions:
            sum += position.dd

        print(sum)
        if curr_min > sum:
            curr_min = sum
            curr_min_positions = positions

    print(curr_min)
    return curr_min_positions



def get_distance_var(lof, frame_oi, frames_dict):
    filtered_frames = []
    print('')
    print('Now in get_distance_var')
    print(lof)
    for f in lof:
        print(f)
        #todo: Load frames only once and pass frames around as paramater
        frames = frames_dict[f]
        filtered_frames.append(filter2_test_j(frames[frame_oi,:,:]))

    print("Getting all the distances.." )
    # Get all the distances using all videos as ref point, thus size of matrix is n^2
    list_of_ref = []
    for frame_ref in filtered_frames:
        list_of_positions = []
        res_trials = parmap.map(image_registration.chi2_shift, filtered_frames, frame_ref)
        # res_trials is array of trials * [dx, dy, edx, edy]
        for res in res_trials:
            list_of_positions.append(Position(res[0], res[1]))
        #for frame in filtered_frames:
        #    dx, dy, edx, edy = image_registration.chi2_shift(frame_ref, frame)
        #    list_of_positions.append(Position(dx, dy))

        list_of_ref.append(list_of_positions)
    print("Finding the min...")
    list_of_positions = find_min_ref(list_of_ref)

    return list_of_positions


class MouseInfo:
    def __init__(self, tag, p2p_x, p2p_y, avg_x, avg_y, n_trials):
        self.tag = tag
        self.p2p_x = p2p_x
        self.p2p_y = p2p_y
        self.avg_x = avg_x
        self.avg_y = avg_y
        self.n_trials = n_trials

def p2p(arr):
    return max(arr)-min(arr)

def do_it_all():
    list_mouse_info = []
    for mouse in mice:
        lof, lofilenames = get_file_list(base_dir, mouse)
        print("Lof: ", lof)
        lop = get_distance_var(lof)
        dx_trials = []
        dy_trials = []
        for position in lop:
            dx_trials.append(position.dx)
        for position in lop:
            dy_trials.append(position.dy)

        peak_x = p2p(dx_trials)
        peak_y = p2p(dy_trials)
        avg_x = np.mean(dx_trials)
        avg_y = np.mean(dy_trials)

        list_mouse_info.append(MouseInfo(mouse, peak_x, peak_y, avg_x, avg_y, len(lop)))

    with open(base_dir+"data.tsv", "w") as file:
        file.write("Tag\tp2p_x\tavg_x\tp2p_y\tavg_y\tn_trials\n")
        for info in list_mouse_info:
            file.write(info.tag + "\t" + str(info.p2p_x) + "\t" + str(info.avg_x) + "\t" + str(info.p2p_y) + "\t" + str(info.avg_y) + "\t" + str(info.n_trials) + "\n")

    print("Done it all!")


def process_frames(frames, freq, mouse, dir):
    print("Fixing paint..")
    mouse = mouse[-3:]
    mask = 0
    with open(dir+mouse+"_paint_mask.raw", "rb") as file:
        mask = np.fromfile(file, dtype=np.float32)

    indices = np.squeeze((mask > 0).nonzero())
    paint_frames = np.zeros((frames.shape[0], len(indices)))
    frames = np.reshape(frames, (frames.shape[0], width*height))

    for i in range(frames.shape[0]):
        paint_frames[i, :] = frames[i, indices]
    print(np.shape(paint_frames))

    mean_paint = np.mean(paint_frames, axis=1)
    mean_paint /= np.mean(mean_paint)

    print(np.shape(mean_paint))


    frames = np.divide(frames.T, mean_paint)
    frames = frames.T

    frames = np.reshape(frames, (frames.shape[0], width, height))

    print("Calculating mean...")
    avg_pre_filt = calculate_avg(frames)

    print("Temporal filter... ", freq.low_limit, "-", freq.high_limit, "Hz")
    frames = cheby_filter(frames, freq.low_limit, freq.high_limit)
    frames += avg_pre_filt

    print("Calculating DF/F0...")
    frames = calculate_df_f0(frames)

    print("Applying MASKED GSR...")
    #frames = gsr(frames)
    frames = masked_gsr(frames, dir+mouse+"_mask.raw")

    #print "Getting SD map..."
    #sd = standard_deviation(frames)

    return frames


def shift_frames(frames, positions):
    print(positions.dx, positions.dy)
    print(frames.shape)
    for i in range(len(frames)):
        frames[i] = image_registration.fft_tools.shift2d(frames[i], positions.dx, positions.dy)

    return frames


def align_frames(mouse, dir, freq):
    lofiles, lofilenames = get_file_list(dir+"Videos/", mouse)
    print(lofilenames)
    lop = get_distance_var(lofiles)

    all_frames = np.asarray(get_video_frames(lofiles), dtype=np.uint8)
    print("Alligning all video frames...")

    all_frames = parmap.starmap(shift_frames, list(zip(all_frames, lop)))
##    for i in range(len(lop)):
##        for frame in all_frames[i]:
##            frame = image_registration.fft_tools.shift2d(frame, lop[i].dx, lop[i].dy)

    print(np.shape(all_frames))

    count = 0
    new_all_frames = parmap.map(process_frames, all_frames, freq, mouse, dir)
    '''
    for frames in all_frames:
        print np.shape(frames)
        save_to_file("Green/"+lofilenames[count][:-4]+"_aligned.raw", frames, np.float32)

        print "Calculating mean..."
        avg_pre_filt = calculate_avg(frames)

        print "Temporal filter..."
        frames = cheby_filter(frames)
        frames += avg_pre_filt
        save_to_file("Green/Cheby/"+lofilenames[count][:-4]+"_BPFilter_0.1-1Hz.raw", frames, np.float32)


        print "Calculating DF/F0..."
        frames = calculate_df_f0(frames)
        save_to_file("Green/DFF/"+lofilenames[count][:-4]+"_DFF.raw", frames, np.float32)

        print "Applying MASKED GSR..."
        #frames = gsr(frames)
        frames = masked_gsr(frames, save_dir+"202_mask.raw")
        save_to_file("Green/GSR/"+lofilenames[count][:-4]+"_GSR.raw", frames, np.float32)


        print "Getting SD map..."
        sd = standard_deviation(frames)
        save_to_file("Green/SD_maps/"+lofilenames[count][:-4]+"_SD.raw", frames, np.float32)

        new_all_frames.append(frames)
        count += 1
    '''
    print("Creating array...")
    new_all_frames = np.asarray(new_all_frames, dtype=np.float32)
    all_frames = np.asarray(all_frames, dtype=np.float32)

    print("Joining Files...")
    new_all_frames = np.reshape(new_all_frames,
                            (new_all_frames.shape[0]*new_all_frames.shape[1],
                            new_all_frames.shape[2],
                            new_all_frames.shape[3]))
    all_frames = np.reshape(all_frames,
                            (all_frames.shape[0]*all_frames.shape[1],
                            all_frames.shape[2],
                            all_frames.shape[3]))

    print("Shapes: ")
    print(np.shape(all_frames))
    print(np.shape(new_all_frames))

    where_are_NaNs = np.isnan(new_all_frames)
    new_all_frames[where_are_NaNs] = 0

    save_to_file("FULL_conc.raw", new_all_frames, np.float32)
    save_to_file("conc_RAW.raw", all_frames, np.float32)
    sd = standard_deviation(new_all_frames)
    save_to_file("FULL_SD.raw", sd, np.float32)

    print("Displaying correlation map...")
    mapper = CorrelationMapDisplayer(new_all_frames)
    mapper.display('spectral', -0.3, 1.0)


def process_frames_evoked(frames):
    #print "Calculating mean..."
    #avg_pre_filt = calculate_avg(frames)

    #print "Temporal filter..."
    #frames = cheby_filter(frames)
    #frames += avg_pre_filt

    print("Calculating DF/F0...")
    frames = calculate_df_f0(frames)

    print("Applying MASKED GSR...")
    frames = gsr(frames)
    frames = masked_gsr(frames, dir+"245_mask.raw")

    return frames


def get_evoked_map(mouse):

    lofiles, lofilenames = get_file_list(base_dir, mouse)
    print(lofilenames)
    lop = get_distance_var(lofiles)

    all_frames = get_video_frames(lofiles)
    print("Alligning all video frames...")

    all_frames = parmap.starmap(shift_frames, list(zip(all_frames, lop)))
    all_frames = np.asarray(all_frames, dtype=np.float32)
    print(np.shape(all_frames))

    new_all_frames = parmap.map(process_frames_evoked, all_frames)

    all_frames = np.reshape(all_frames,
                            (all_frames.shape[0]*all_frames.shape[1],
                            all_frames.shape[2],
                            all_frames.shape[3]))
    save_to_file("conc_RAW.raw", all_frames, np.float32)


    print("Creating array..")
    new_all_frames = np.asarray(new_all_frames, dtype=np.float32)
    print("Averaging together...")
    new_all_frames = np.mean(new_all_frames, axis=0)

    print(np.shape(new_all_frames))


    save_to_file("evoked_trial_noBP_GSR.raw", new_all_frames, np.float32)



def get_corr_maps(mouse, dir, freq, coords):
    str_freq = str(freq.low_limit) + "-" + str(freq.high_limit) + "Hz"
    lofiles, lofilenames = get_file_list(dir+"Videos/", mouse)
    print(lofilenames)
    lop = get_distance_var(lofiles)

    with open(dir+mouse+'_lop.txt','w') as file:
        for pos in lop:
            to_write=str(pos.dx)+' '+str(pos.dy)+'\n'
            file.write(to_write)
    '''
    all_frames = np.asarray(get_video_frames(lofiles), dtype=np.uint8)
    print "Alligning all video frames..."

    all_frames = parmap.starmap(shift_frames, zip(all_frames, lop))

    print np.shape(all_frames)

    count = 0
    new_all_frames = parmap.map(process_frames, all_frames, freq, mouse, dir)

    print "Creating array..."
    new_all_frames = np.asarray(new_all_frames, dtype=np.float32)
    all_frames = np.asarray(all_frames, dtype=np.float32)

    print "Joining Files..."
    new_all_frames = np.reshape(new_all_frames,
                            (new_all_frames.shape[0]*new_all_frames.shape[1],
                            new_all_frames.shape[2],
                            new_all_frames.shape[3]))

    print "Shapes: "
    print np.shape(all_frames)
    print np.shape(new_all_frames)

    where_are_NaNs = np.isnan(new_all_frames)
    new_all_frames[where_are_NaNs] = 0

    save_to_file(dir,"processed_conc_"+mouse+"_"+str_freq+".raw", new_all_frames, np.float32)
    sd = standard_deviation(new_all_frames)
    save_to_file(dir,"all_frames_SD"+mouse+"_"+str_freq+".raw", sd, np.float32)

    for coord in coords:
        corr_map = get_correlation_map(coord.x, coord.y, new_all_frames)

        save_to_file(dir, "All_Maps/"+mouse+"_map_"+str(coord.x)+","+str(coord.y)+"_"+str_freq+".raw", corr_map, dtype=np.float32)

    #print "Displaying correlation map..."
    #mapper = CorrelationMapDisplayer(new_all_frames)
    #mapper.display('spectral', -0.3, 1.0)

    print "All done!! :))"
    '''

class FrequencyLimit:
    def __init__(self, low, high):
        self.low_limit = low
        self.high_limit = high

class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def get_correlation_map(seed_x, seed_y, frames):
    seed_pixel = np.asarray(frames[:, seed_x, seed_y], dtype=np.float32)

    print(np.shape(seed_pixel))
    # Reshape into time and space
    frames = np.reshape(frames, (frames.shape[0], width*height))
    print(np.shape(frames))
    print('Getting correlation... x=', seed_x, ", y=", seed_y)

    correlation_map = parmap.map(corr, frames.T, seed_pixel)
    correlation_map = np.asarray(correlation_map, dtype=np.float32)
    correlation_map = np.reshape(correlation_map, (width, height))
    print(np.shape(correlation_map))

    return correlation_map

'''
###BEGIN MAIN
#do_it_all()

#coords = [Coordinate(136, 222),
#          Coordinate(134, 175),
#          Coordinate(173, 190)]
#
#frequencies = [FrequencyLimit(0.1, 3.),
#               FrequencyLimit(0.25, 3.),
#               FrequencyLimit(0.5, 3.),
#               FrequencyLimit(0.75, 3.)]

coords= [Coordinate(136,222)]

frequencies = [FrequencyLimit(.1,3.)]

for i in range(len(mice)):
     for freq in frequencies:
         get_corr_maps(mice[i], base_dir[i], freq, coords)

###END MAIN END MAIN END MAIN
'''