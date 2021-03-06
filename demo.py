import dash
import parse_mpd as pm
import os
import sys
import getopt
import dash as ds
import netspeed as netspeed
import math

def Init(dash):
    dash.bitrate = dash.mpd["bitrates"][0]
    init_size = dash.mpd[dash.bitrate][0]
    while init_size > 0:
        init_size = init_size - dash.sim_inteval * dash.get_throughput()
        dash.time = dash.time + dash.sim_inteval
    #dash.log(str(1) + " Downloaded!")
    dash.buffer_len = dash.segment_len
    #dash.log("Buffer Level: " + str(dash.buffer_len))
    dash.chunk_index = dash.chunk_index + 1
    dash.select(1)

def Demo(mpd_path, log_path):
    dash = ds.Dash(mpd_path, log_path)
    Init(dash)
    while True:
        Tick(dash)

def BBA(dash):
    max_buffer = dash.max_buffer
    #r = max_buffer * 0.3
    #cu = max_buffer * (0.9 - 0.3)
    r = dash.r
    cu = dash.cu
    T = dash.get_throughput()
    quality = dash.quality
    buffer_len = dash.buffer_len
    new_quality = quality
    max_quality = len(dash.mpd["bitrates"])
   
    
    quality_plus = quality
    quality_minus = quality
    if quality > max_quality:
        quality_plus = max_quality
    else:
        quality_plus = quality + 1

    if quality <= 1 :
        quality_minus = 1
    else:
        quality_minus = quality - 1

    if buffer_len <= r :
        new_quality = 1
    elif buffer_len >= (r + cu) :
        new_quality = max_quality
    
    tmp = 1 + (buffer_len - r) * (max_quality - 1) / cu
    if tmp >= quality_plus :
        new_quality = math.floor(tmp)
    elif tmp <= quality_minus:
        new_quality = math.ceil(tmp)
    else:
        new_quality = quality
        
    dash.select(new_quality)

def BBA1(dash):
    max_buffer = dash.max_buffer
    #r = max_buffer * 0.3
    #cu = max_buffer * (0.9 - 0.3)
    r = dash.r
    cu = dash.cu
    T = dash.get_throughput()
    quality = dash.quality
    buffer_len = dash.buffer_len
    new_quality = quality
    max_quality = len(dash.mpd["bitrates"])
    last_chunk_index = (dash.chunk_index - 1)
    last_dltime = dash.dltime[last_chunk_index]
    duration = dash.segment_len

    r = r + (last_dltime - duration)
    if r < 2 * duration :
        r = 2 * duration
    elif r > 0.5 * max_buffer :
        r = 0.5 * max_buffer
    dash.r = r


    quality_plus = quality
    quality_minus = quality
    if quality > max_quality:
        quality_plus = max_quality
    else:
        quality_plus = quality + 1

    if quality <= 1 :
        quality_minus = 1
    else:
        quality_minus = quality - 1

    if buffer_len <= r :
        new_quality = 1
    elif buffer_len >= (r + cu) :
        new_quality = max_quality
    
    tmp = 1 + (buffer_len - r) * (max_quality - 1) / cu
    if tmp >= quality_plus :
        new_quality = math.floor(tmp)
    elif tmp <= quality_minus:
        new_quality = math.ceil(tmp)
    else:
        new_quality = quality
        
    dash.select(new_quality)

def BBA2(dash):
    max_buffer = dash.max_buffer
    #r = max_buffer * 0.3
    #cu = max_buffer * (0.9 - 0.3)
    r = dash.r
    cu = dash.cu
    T = dash.get_throughput()
    quality = dash.quality
    buffer_len = dash.buffer_len
    new_quality = quality
    new_quality_startup = 1
    max_quality = len(dash.mpd["bitrates"])
    last_chunk_index = (dash.chunk_index - 1)
    last_dltime = dash.dltime[last_chunk_index]
    duration = dash.segment_len
    last_buffer_len = dash.last_buffer_len


    r = r + (last_dltime - duration)
    if r < 2 * duration :
        r = 2 * duration
    elif r > 0.5 * max_buffer :
        r = 0.5 * max_buffer
    dash.r = r

    if buffer_len < last_buffer_len :
        dash.startup = 0

    if dash.startup == 1 :
        if buffer_len < r :
            if duration > dash.bba2_threshold * last_dltime:
                new_quality_startup = quality + 1
                dash.bba2_threshold = dash.bba2_threshold - 1
            else:
                new_quality_startup = quality
        else:
            dash.bba2_threshold = 2
            if duration > dash.bba2_threshold * last_dltime:
                new_quality_startup = quality + 1
            else:
                new_quality_startup = quality      

    quality_plus = quality
    quality_minus = quality
    if quality > max_quality:
        quality_plus = max_quality
    else:
        quality_plus = quality + 1
    
    if quality <= 1 :
        quality_minus = 1
    else:
        quality_minus = quality - 1

    if buffer_len <= r :
        new_quality = 1
    elif buffer_len >= (r + cu) :
        new_quality = max_quality
    
    tmp = 1 + (buffer_len - r) * (max_quality - 1) / cu
    if tmp >= quality_plus :
        new_quality = math.floor(tmp)
    elif tmp <= quality_minus:
        new_quality = math.ceil(tmp)
    else:
        new_quality = quality

    if new_quality > new_quality_startup :
        dash.startup = 0
    else:
        new_quality = new_quality_startup
            
    dash.select(new_quality)

def algorithm1(dash):
    max_buffer = dash.max_buffer
    r = max_buffer * 0.3
    cu = max_buffer * (0.9 - 0.3)
    T = dash.get_throughput()
    quality = dash.quality
    buffer_len = dash.buffer_len
    new_quality = quality
    max_quality = len(dash.mpd["bitrates"])
    next_chunks_size = dash.get_chunks_size()
    duration = dash.segment_len

    ref = 1
    for i in range(1, max_quality):
        if next_chunks_size[i] / duration > T:
            ref = i - 1
            break
    
    if buffer_len <= r :
        for i in range(1, max_quality):
            if next_chunks_size[i] > (duration - buffer_len) * T:
                tmp = i - 1
                break
        new_quality = max(tmp,1)
    elif buffer_len >= (r + cu) :
        new_quality = max_quality
    else:
        new_quality = ref

    dash.select(new_quality)

def algorithm2(dash):
    max_buffer = dash.max_buffer
    r = max_buffer * 0.3
    cu = max_buffer * (0.9 - 0.3)
    T = dash.get_throughput()
    quality = dash.quality
    buffer_len = dash.buffer_len
    new_quality = quality
    max_quality = len(dash.mpd["bitrates"])
    next_chunks_size = dash.get_chunks_size()
    duration = dash.segment_len

    ref = 1
    for i in range(1, max_quality):
        if next_chunks_size[i] / duration > T:
            ref = i - 1
            break
    
    if buffer_len <= r :
        ref = max(ref-1,1)
        if ref < quality:
            for i in range(1, max_quality):
                if next_chunks_size[i] > (duration - buffer_len) * T:
                    tmp = i - 1
                    breakzo
            new_quality = max(tmp,1)
        else:
            new_quality = ref
    elif buffer_len >= (r + cu) :
        new_quality = max(ref,quality)
    else:
        if ref < quality :
            new_quality = quality
        else:
            new_quality = ref

    dash.select(new_quality)

def PBAC(dash):
    max_buffer = dash.max_buffer
    r = max_buffer * 0.3
    cu = max_buffer * (0.9 - 0.3)
    T = dash.get_throughput()
    quality = dash.quality
    buffer_len = dash.buffer_len
    new_quality = quality
    max_quality = len(dash.mpd["bitrates"])
    next_chunks_size = dash.get_chunks_size()
    duration = dash.segment_len

    ref = 1
    for i in range(1, max_quality):
        if next_chunks_size[i] / duration > T:
            ref = i - 1
            break
    
    if buffer_len <= r :
        ref = max(ref-1,1)
        if ref < quality:
            for i in range(1, max_quality):
                if next_chunks_size[i] > (duration - buffer_len) * T:
                    tmp = i - 1
                    break
            new_quality = max(tmp,1)
        else:
            new_quality = ref
    elif buffer_len >= (r + cu) :
        #new_quality = max_quality
        new_quality = max(ref,quality)
    else:
        if ref < quality :
            new_quality = quality
        else:
            buffergap = duration * (T/next_chunks_size[ref]-1)
            bufferemp = max_buffer - buffer_len
            if buffergap > 0.15 * bufferemp:
                new_quality = ref
            else:
                new_quality = ref - 1

    dash.select(new_quality)

def PBAC2(dash):
    max_buffer = dash.max_buffer
    r = max_buffer * 0.3
    cu = max_buffer * (0.9 - 0.3)
    T = dash.get_throughput()
    quality = dash.quality
    buffer_len = dash.buffer_len
    new_quality = quality
    max_quality = len(dash.mpd["bitrates"])
    next_chunks_size = dash.get_chunks_size()
    duration = dash.segment_len

    ref = 1
    for i in range(1, max_quality):
        if next_chunks_size[i] / duration > T:
            ref = i - 1
            break
    
    if buffer_len <= r :
        ref = max(ref-1,1)
        if ref < quality:
            for i in range(1, max_quality):
                if next_chunks_size[i] > (duration - buffer_len) * T:
                    tmp = i - 1
                    break
            new_quality = max(tmp,1)
        else:
            new_quality = ref
    elif buffer_len >= (r + cu) :
        new_quality = max_quality
        #new_quality = max(ref,quality)
    else:
        if ref < quality :
            new_quality = quality
        else:
            buffergap = duration * (T/next_chunks_size[ref]-1)
            bufferemp = max_buffer - buffer_len
            if buffergap > 0.15 * bufferemp:
                new_quality = ref
            else:
                new_quality = ref - 1

    dash.select(new_quality)

def Tick(dash):
    dash.tick()
    if dash.check() == True:
        dash.get_throughput()
        return
    #BBA(dash)
    #BBA1(dash)
    BBA2(dash)
    #algorithm1(dash)
    #algorithm2(dash)
    #PBAC(dash)
    #PBAC2(dash)
    
if __name__ == "__main__":
    mpd_path = sys.argv[1]
    log_path = sys.argv[2]
    Demo(mpd_path, log_path)
