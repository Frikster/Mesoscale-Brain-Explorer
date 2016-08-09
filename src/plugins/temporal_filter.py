# on button click!

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Widget(QWidget):
    def temporal_filter(self):
        # Collect all user-defined variables (and variables immediately inferred from user-selections)
        fileName = str(self.sidePanel.imageFileList.currentItem().text())
        width = int(self.sidePanel.vidWidthValue.text())
        height = int(self.sidePanel.vidHeightValue.text())
        frame_rate = int(self.sidePanel.frameRateValue.text())
        f_high = float(self.sidePanel.f_highValue.text())
        f_low = float(self.sidePanel.f_lowValue.text())
        dtype_string = str(self.sidePanel.dtypeValue.text())

        frames = fj.load_frames(fileName, width, height, dtype_string)

        # Compute df/d0 and save to file
        avg_frames = fj.calculate_avg(frames)
        frames = fj.cheby_filter(frames, f_low, f_high, frame_rate)
        frames += avg_frames
        frames = fj.calculate_df_f0(frames)
        np.save(os.path.expanduser('~/Downloads/')+"dfoverf0_avg_framesIncl", frames)
        #frames.astype(dtype_string).tofile(os.path.expanduser('~/Downloads/')+"dfoverf0_avg_framesIncl.raw")
        print("temporal filter saved to"+os.path.expanduser(os.path.expanduser('~/Downloads/')+"dfoverf0_avg_framesIncl"))
        # self.filtered_frames = frames

        process = psutil.Process(os.getpid())
        print process.memory_info().rss

class MyPlugin:
  def __init__(self, project):
    self.name = 'Temporal filter'
    self.widget = Widget()

  def run(self):
    pass
