import os
import sys
import string
import time
import parse_mpd as pm
import netspeed as netspeed

class Dash:
    def __init__(self, mpd_dir, log_dir):
        self.fp = open("log_" + time.ctime(), "w")
        self.buffer_len = 0
        self.mpd = pm.parse_mpd(mpd_dir)
        self.buffer_empty_count = 0
        self.switch_count = 0
        self.time = 0
        self.isempty = 0
        self.last_isempty = 0
        self.isdownloading = 0
        self.chunk_downloaded = 0#the one downloading
        self.chunk_size = 0
        self.last_bitrate = 0
        self.bitrate = 0
        self.quality = 1
        self.netspeed = 0
        self.last_netspeed = 0
        self.min_buffer_time = self.mpd["min_buffer"]
        self.segment_len = self.mpd["seglen"]
        self.chunk_index = 1
        self.sim_inteval = 0.1
        self.finished = 0
        self.max_buffer = 40
        self.r = self.max_buffer * 0.3
        self.cu = self. max_buffer * (0.9 - 0.3)
        self.throughput = netspeed.Throughput(log_dir)
        self.ave_bitrate = 0
        self.total_bitrate = 0
        self.dltime = [0, 0]

    def __del__(self):
        self.log("Finished!")
        self.log("Switch count: " + str(self.switch_count))
        self.log("Rebuffer count: " + str(self.buffer_empty_count))
        self.log("Average bitrate: " + str(self.ave_bitrate))
        self.fp.close()
    
    def tick(self):
        #update basic variables
        self.time = self.time + self.sim_inteval
        self.buffer_len = self.buffer_len - self.sim_inteval
        self.last_isempty = self.isempty
        #self.log("T " + str(self.netspeed))

        if self.buffer_len >= self.max_buffer - self.segment_len:
            #self.log("Sleep " + str(self.sim_inteval) + 's')
            return
       
        if self.buffer_len <= 0:
            self.buffer_len = 0
        #    self.log("Buffer Dry Out!")
            self.isempty = 1
        else:
            self.isempty = 0
        
        if self.last_isempty == 0 and self.isempty == 1:
            self.buffer_empty_count = self.buffer_empty_count + 1
        #print self.isdownloading, self.can_download
        #time.sleep(0.5)
        

        if self.can_download == 1:
            self.chunk_downloaded = self.chunk_downloaded + self.sim_inteval * self.last_netspeed
            #print self.chunk_downloaded, self.chunk_size
            if self.chunk_downloaded >= self.chunk_size:
                self.isdownloading = 0
                self.dltime[self.chunk_index] = self.time - self.dltime[self.chunk_index]
                #self.log("Download time " + str(self.dltime[self.chunk_index]))
                #self.log(str(self.chunk_index) + " Downloaded!")
                self.chunk_index = self.chunk_index + 1
                self.chunk_downloaded = 0
                self.buffer_len = self.buffer_len + self.segment_len
                #self.log("Buffer Level: " + str(self.buffer_len))
                self.can_download = 0
            else:
                #pass
                self.isdownloading = 1
        

        tmp_bps = self.mpd["bitrates"][0]
        chunk_num = len(self.mpd[tmp_bps])
        #print chunk_num
        if self.chunk_index >= chunk_num - 1:
            self.finished = 1
        else:
            self.finished = 0

    def log(self, msg):
        info = str(self.time) + ' : ' + msg + '\n'
        #print info
        self.fp.write(info)
    
    def check(self):
        if self.finished == 1:
            #self.log("Finished!")
            exit()
        if self.isdownloading == 1:
            return True
        elif self.isdownloading == 0:
            return False

    def select(self, rate):
        #the rate must be index
        self.can_download = 1
        rate = int(rate)
        if rate < 1:
            rate = 1
        if rate >= len(self.mpd["bitrates"]):
            rate = len(self.mpd["bitrates"])
        self.quality = rate
        if rate < 100:
            rate = self.mpd["bitrates"][rate - 1]

        self.last_bitrate = self.bitrate
        self.bitrate = rate
        self.total_bitrate = self.total_bitrate + rate
        self.ave_bitrate = self.total_bitrate / self.chunk_index
        #self.log("Begin Download: " + str(self.chunk_index) + ", bitrate: " + str(self.bitrate) + ", quality: " + str(self.quality)  )
        self.dltime.append(self.time)
        if (self.last_bitrate != self.bitrate):
            self.switch_count = self.switch_count + 1
            #self.log(str(self.chunk_index) + "Rate switched!")
        #print rate, self.chunk_index,len( self.mpd[rate] )
        self.chunk_size = self.mpd[rate][self.chunk_index]
        self.isdownloading = 1        

    def get_throughput(self):
        self.last_netspeed = self.netspeed
        if ((self.time % 1) < 0.05 or (self.time % 1) > 0.95):
            self.netspeed = self.throughput.get_speed()
        else:
            self.netspeed = self.netspeed
        return self.netspeed

    def get_chunks_size(self):
        sizes = []
        for v in self.mpd["bitrates"]:
            sizes.append( self.mpd[v][self.chunk_index] )
        return sizes


