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
        self.segmenet_len = self.mpd["seglen"]
        self.chunk_index = 0
        self.sim_inteval = 0.1
        self.finished = 0
        self.throughput = netspeed.Throughput(log_dir)

    def __del__(self):
        self.fp.close()
    
    def tick(self):
        #update basic variables
        self.time = self.time + self.sim_inteval
        self.buffer_len = self.buffer_len - self.sim_inteval
        self.last_isempty = self.isempty
        
        if self.buffer_len <= 0:
            self.buffer_len = 0
            self.log("Buffer Dry Out!")
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
                self.log(str(self.chunk_index) + " Downloaded!")
                self.chunk_index = self.chunk_index + 1
                self.chunk_downloaded = 0
                self.buffer_len = self.buffer_len + self.segmenet_len
                self.log("Buffer Level: " + str(self.buffer_len))
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
            self.log("Finished!")
            exit()
        if self.isdownloading == 1:
            return True
        elif self.isdownloading == 0:
            return False

    def select(self, rate):
        self.can_download = 1
        if rate < 100:
            rate = self.mpd["bitrates"][rate - 1]
        
        self.last_bitrate = self.bitrate
        self.bitrate = rate
        self.log("Begin Download: " + str(self.chunk_index) + ", bitrate: " + str(self.bitrate))
        if (self.last_bitrate != self.bitrate):
            self.buffer_empty_count = self.buffer_empty_count + 1
            self.log(str(self.chunk_index) + "Rate switched!")
        #print rate, self.chunk_index,len( self.mpd[rate] )
        self.chunk_size = self.mpd[rate][self.chunk_index]
        self.isdownloading = 1        

    def get_throughput(self):
        self.last_netspeed = self.netspeed
        self.netspeed = self.throughput.get_speed()
        return self.netspeed

    def get_chunks_size(self):
        sizes = []
        for v in self.mpd["bitrates"]:
            sizes.append( self.mpd[v][self.chunk_index] )
        return sizes


