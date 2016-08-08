import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from scipy.stats.stats import pearsonr
from scipy import ndimage
#from joblib import Parallel, delayed
#import multiprocessing
import parmap
import image_registration
from PIL import Image
from numpy import *
import tifffile as tiff


#from libtiff import TIFF

#M1312000377_1438367187.563086.raw
#processed_data/Concatenated Stacks.raw
#file_to_filter = "/media/user/DataFB/AutoHeadFix_Data/0731/EL_LRL/Videos/M2015050115_1438365772.086721.raw"
#file_to_filter2 = "/media/user/DataFB/AutoHeadFix_Data/0731/EL_LRL/Videos/M2015050115_1438366080.539013.raw"
#file_to_save = "/media/user/DataFB/AutoHeadFix_Data/0731/EL_LRL/global_signal.rawf"
#corrfile_to_save = "/media/ch0l1n3/DataFB/AutoHeadFix_Data/0802/EL_LRL/corr.rawf"
#sd_file = "/media/user/DataFB/AutoHeadFix_Data/0731/EL_LRL/mean_filter.rawf"

#save_dir = "/media/user/DataFB/AutoHeadFix_Data/0731/EL_LRL/"

#starting_frame = 100

def load_raw(filename, width, height, dat_type):
    dat_type = np.dtype(dat_type)

    with open(filename, "rb") as file:
        frames = np.fromfile(file, dtype=dat_type)
    try:
        total_number_of_frames = int(np.size(frames) / (width * height * 3))
        print("n_frames: " + str(total_number_of_frames))
        frames = np.reshape(frames, (total_number_of_frames, width, height, 3))
        frames = frames[:, :, :, 1]
    except:
        print("Reshape failed. Attempting single channel")
        total_number_of_frames = int(np.size(frames)/(width*height))
        print("n_frames: "+str(total_number_of_frames))
        frames = np.reshape(frames, (total_number_of_frames, width, height))
    #todo: note that you got rid of starting_frame!
    # frames = frames[starting_frame:, :, :, 1]
    frames = np.asarray(frames, dtype=dat_type)

    return frames

def load_tiff(filename):
    imarray = tiff.imread(filename)
    return imarray

def load_npy(filename):
    frames = np.load(filename)
    frames[isnan(frames)] = 0
    return frames

def load_frames(filename, width, height, dat_type):
    if filename.endswith('.tif'):
        return load_tiff(filename)
    elif filename.endswith(".raw"):
         return load_raw(filename, width, height, dat_type)
    elif filename.endswith(".npy"):
        return load_npy(filename)
    else:
        print("unsupported file type")

def get_frames(rgb_file, width, height, dat_type):

    if(rgb_file.endswith(".tif")):
        imarray = tiff.imread(rgb_file)
        return imarray

    if (rgb_file.endswith(".raw")):
        dat_type = np.dtype(dat_type)
        with open(rgb_file, "rb") as file:
            frames = np.fromfile(file, dtype=dat_type)
            total_number_of_frames = int(np.size(frames) / (width * height * 3))
            print("n_frames: " + str(total_number_of_frames))
            frames = np.reshape(frames, (total_number_of_frames, width, height, 3))
            #todo: note that you got rid of starting_frame!
            # frames = frames[starting_frame:, :, :, 1]
            frames = frames[:, :, :, 1]
            frames = np.asarray(frames, dtype=dat_type)
            return frames

    if (rgb_file.endswith(".npy")):
        frames = np.load(rgb_file)
        frames[isnan(frames)] = 0
        return frames

    print("unsupported file type")
        ########
        # Cat method
        # img = Image.open(rgb_file)
        # n_pixels = img.height
        # n_frames = img.n_frames
        #
        # images_raw = np.zeros((n_frames, n_pixels, n_pixels), dtype=dat_type)
        #
        # print("n_frames: " + str(n_frames))
        # for i in range(0, n_frames, 1):
        #     img.seek(i)
        #     #print "Loading frame: ", i
        #     #images_raw [i] = np.flipud(np.fliplr(np.float16(img))) #FLIP IMAGES FOR Experiments Nov and Dec 2015
        #     # todo: dtype needed?
        #     images_raw[i] = np.array(img)
        #     #images_raw[i] = np.array(img, dtype=dat_type)
        #imarray = images_raw

        ######
        # # plt method
        # I = plt.imread(rgb_file)
        #
        # #tifflib method
        # # to open a tiff file for reading:
        # tif = TIFF.open(rgb_file, mode='r')
        # # to read an image in the currect TIFF directory and return it as numpy array:
        # image = tif.read_image()
        # # to read all images in a TIFF file:
        # for image in tif.iter_images(): # do stuff with image
        #     image = tif.read_image()
        #
        # # to open a tiff file for writing:
        # tif = TIFF.open('filename.tif', mode='w')
        # #to write a image to tiff file
        # tif.write_image(image)
        #
        # #PIL method
        # im = Image.open(rgb_file)
        # imarray = np.array(im)
        #return imarray


def get_green_frames(g_file, width, height, dat_type):
    if(g_file.endswith(".tif")):
        imarray = tiff.imread(g_file)
        return imarray

    if (g_file.endswith(".raw")):
        dat_type = np.dtype(dat_type)
        with open(g_file, "rb") as file:
            frames = np.fromfile(file, dtype=dat_type)
            total_number_of_frames = int(np.size(frames)/(width*height))
            print("n_frames: "+str(total_number_of_frames))
            frames = np.reshape(frames, (total_number_of_frames, width, height))
            frames = np.asarray(frames, dtype=dat_type)
        return frames

    if (g_file.endswith(".npy")):
        frames = np.load(g_file)
        return frames

        # ########
        # # Cat method
        # img = Image.open(g_file)
        # n_pixels = img.height
        # n_frames = img.n_frames
        #
        # images_raw = np.zeros((n_frames, n_pixels, n_pixels), dtype=dat_type)
        #
        # print("n_frames: " + str(n_frames))
        # for i in range(0, n_frames, 1):
        #     img.seek(i)
        #     #print "Loading frame: ", i
        #     #images_raw [i] = np.flipud(np.fliplr(np.float16(img))) #FLIP IMAGES FOR Experiments Nov and Dec 2015
        #     images_raw[i] = np.array(img, dtype=dat_type) #2016-1-11 2016-1-14 experiment no flipping needed
        # imarray = images_raw
        #
        # return imarray



def get_processed_frames(rgb_file,width,height):
    with open(rgb_file, "rb") as file:
        frames = np.fromfile(file, dtype=np.float32)
        total_number_of_frames = int(np.size(frames)/(width*height))
        print(total_number_of_frames)
        frames = np.reshape(frames, (total_number_of_frames, width, height))
        frames = np.asarray(frames, dtype=np.float32)
        total_number_of_frames = frames.shape[0]
    return frames

def filt(pixel, b, a):
    return signal.filtfilt(b, a, pixel)

def cheby_filter(frames, low_limit, high_limit,frame_rate):
    nyq = frame_rate/2.0
    low_limit = low_limit/nyq
    high_limit = high_limit/nyq
    order = 4
    rp = 0.1
    Wn = [low_limit, high_limit]

    b, a = signal.cheby1(order, rp, Wn, 'bandpass', analog=False)
    print("Filtering...")
    frames = signal.filtfilt(b, a, frames, axis=0)
    #frames = parmap.map(filt, frames.T, b, a)
    #for i in range(frames.shape[-1]):
    #    frames[:, i] = signal.filtfilt(b, a, frames[:, i])
    print("Done!")
    return frames

def calculate_avg(frames):
    return np.mean(frames, axis=0)

def calculate_df_f0(frames):
    print(frames.shape)
    baseline = np.mean(frames, axis=0)
    frames = np.divide(np.subtract(frames, baseline), baseline)
    where_are_NaNs = isnan(frames)
    frames[where_are_NaNs] = 0
    return frames

def save_to_file(dir, filename, frames, dtype):
    with open(dir+filename, "wb") as file:
        frames.astype(dtype).tofile(file)


def gsr(frames,width,height):

    frames[isnan(frames)] = 0

    # Reshape into time and space
    frames = np.reshape(frames, (frames.shape[0], width*height))
    mean_g = np.mean(frames, axis=1)
    g_plus = np.squeeze(np.linalg.pinv([mean_g]))

    beta_g = np.dot(g_plus, frames)

    print(np.shape(mean_g))

    print(np.shape(beta_g))

    global_signal = np.dot(np.asarray([mean_g]).T, [beta_g])

    #save_to_file(file_to_save, global_signal, np.float32)

    frames = frames - global_signal

    frames = np.reshape(frames, (frames.shape[0], width, height))
    return frames

def masked_gsr(frames, mask_filename,width,height):
    with open(mask_filename, "rb") as file:
        mask = np.fromfile(file, dtype=np.uint8)


    mask = np.asarray(mask, dtype=np.float32)
    mask[isnan(mask)] = 0
    print(mask.shape)
    indices = np.squeeze((mask > 0).nonzero())
    print(np.shape(indices))
    brain_frames = np.zeros((frames.shape[0], len(indices)))
    frames = np.reshape(frames, (frames.shape[0], width*height))

    for i in range(frames.shape[0]):
        brain_frames[i, :] = frames[i, indices]



    mean_g = np.mean(brain_frames, axis=1)
    g_plus = np.squeeze(np.linalg.pinv([mean_g]))

    beta_g = np.dot(g_plus, frames)

    print(np.shape(mean_g))
    print(np.shape(beta_g))
    global_signal = np.dot(np.asarray([mean_g]).T, [beta_g])
    frames = frames - global_signal
    frames = np.reshape(frames, (frames.shape[0], width, height))
    return frames

def standard_deviation(frames):
    return np.std(frames, axis=0)

def generate_mean_filter_kernel(size):
    kernel = 1.0/(size * size) * np.array([[1]*size]*size)
    return kernel

def filter2_test(frames, frame_no):
    kernel = generate_mean_filter_kernel(8)
    frame = ndimage.convolve(frames[frame_no], kernel, mode='constant', cval=0.0)
    return frames[frame_no] - frame

def filter2_test_j(frame):
    kernel = generate_mean_filter_kernel(8)
    framek = ndimage.convolve(frame, kernel, mode='constant', cval=0.0)
    return frame - framek

def apply_shift(shift_corr, frames2):
    row, col = np.unravel_index(np.argmax(shift_corr), shift_corr.shape)

    for frame2 in frames2:
        ndimage.interpolation.shift(frame2, [0, col-128], frame2, mode='constant')
    print(row, " ", col)
    return frames2

def corr(pixel, seed_pixel):
    return pearsonr(pixel, seed_pixel)[0]


class CorrelationMapDisplayer:
    def __init__(self, frames):
        print("Calling the constructor.")
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        # calculate initial map at center pixel
        print((frames.shape[0]/2))
        print((frames.shape[1]/2))
        print((frames.shape[2]/2))
        # TODO: Is it correct for the indices to be [0] and [1] Jeff (answer is no I think)
        # Todo: Uncomment for duh reasons
        #self.image = self.get_correlation_map(frames.shape[1]/2, frames.shape[2]/2, frames)

        self.image = self.get_correlation_map(175, 75, frames)
        self.imgplot = self.ax.imshow(self.image)
        self.canvas = self.fig.canvas
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.frames = frames
        self.count = 0

    def display(self, c_map, low, high):
        self.c_map = c_map
        self.low = low
        self.high = high
        #self.imgplot.set_cmap(c_map)
        self.imgplot.set_clim(low, high)
        self.fig.colorbar(self.imgplot)
        plt.show()

    def onclick(self, event):
        print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
        event.button, event.x, event.y, event.xdata, event.ydata))
        # X and Y must be flipped to have correct dimmensions!
        self.image = self.get_correlation_map(int(event.ydata), int(event.xdata), self.frames)

        self.imgplot = self.ax.imshow(self.image)
        #self.imgplot.set_cmap(self.c_map)
        self.imgplot.set_clim(self.low, self.high)

        self.canvas.draw()
        save_to_file("Maps/map_" + str(self.count) + ".raw", self.image, np.float32)
        self.count += 1

    def get_correlation_map(self, seed_x, seed_y, frames):
        print((seed_x,seed_y))
        seed_pixel = np.asarray(frames[:, seed_x, seed_y], dtype=np.float32)

        print(np.shape(seed_pixel))
        width=frames.shape[1]
        height=frames.shape[2]
        # Reshape into time and space
        frames = np.reshape(frames, (frames.shape[0], width*height))

        print(np.shape(frames))
        #correlation_map = []
        print('Getting correlation...')
        #correlation_map = Parallel(n_jobs=4, backend="threading")(delayed(corr)(pixel, seed_pixel) for pixel in frames.T)
        #correlation_map = []
        #for i in range(frames.shape[-1]):
        #    correlation_map.append(pearsonr(frames[:, i], seed_pixel)[0])
        # Todo: NaN's generated via this line. Why?
        correlation_map = parmap.map(corr, frames.T, seed_pixel)
        #correlation_map = map(corr, frames.T, seed_pixel)
        correlation_map = np.asarray(correlation_map, dtype=np.float32)
        correlation_map = np.reshape(correlation_map, (width, height))
        print(np.shape(correlation_map))

        return correlation_map

def display_image(image, c_map, low_end_limit, high_end_limit, frames):
    fig = plt.figure()
    ax = fig.add_subplot(111)

    imgplot = ax.imshow(image)

    imgplot.set_cmap(c_map)
    imgplot.set_clim(low_end_limit, high_end_limit)
    fig.colorbar(imgplot)

    displayer = CorrelationMapDisplayer(fig, image, frames)

    plt.show()

def get_correlation_map(seed_x, seed_y, frames):
    print((seed_x,seed_y))
    seed_pixel = np.asarray(frames[:, seed_x, seed_y])

    #print(np.shape(seed_pixel))
    width = frames.shape[1]
    height = frames.shape[2]
    # Reshape into time and space
    frames[frames==0]=np.nan
    frames = np.reshape(frames, (frames.shape[0], width*height))

    print(np.shape(frames))
    #correlation_map = []
    print('Getting correlation...')
    #correlation_map = Parallel(n_jobs=4, backend="threading")(delayed(corr)(pixel, seed_pixel) for pixel in frames.T)
    #correlation_map = []
    #for i in range(frames.shape[-1]):
    #    correlation_map.append(pearsonr(frames[:, i], seed_pixel)[0])
    # Todo: NaN's generated via this line. Why?
    correlation_map = parmap.map(corr, frames.T, seed_pixel)
    #correlation_map = parmap.map(corr, frames.T, seed_pixel)
    #correlation_map = np.asarray(correlation_map, dtype=np.float32)
    correlation_map = np.reshape(correlation_map, (width, height))
    #print(np.shape(correlation_map))

    return correlation_map


