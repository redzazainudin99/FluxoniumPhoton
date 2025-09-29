#this is to check the time delay between the readout pulse and digitizer pulse

import os

import matplotlib.pyplot as plt
import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer

from sequence_parser import Sequence
from setup_td import *
from tqdm import tqdm
# from setup_td_pulses import *

measurement_name = os.path.basename(__file__)[:-3]



def photon_sequence (virtualz, phase, draw_end = False):
    sequence = Sequence([ge_drive_port,gf_drive_port, JPA_port, digi_port])
        
    #reset pulse resets to 1 state
    sequence.add(Square(amplitude=gf_pi.params['amplitude'], duration=5000), gf_drive_port, copy = False)   #reset pulse
    
    if virtualz ==True:
        sequence.add(VirtualZ(np.pi), ge_drive_port,copy = False)
    sequence.call(ge_flat_halfpi_seq)
    if virtualz ==True:
        sequence.add(VirtualZ(-np.pi), ge_drive_port,copy = False)
    sequence.trigger([ge_drive_port,gf_drive_port,])
    sequence.call(gf_pi_seq)

    sequence.add(ResetPhase(phase = phase), JPA_port,copy = False)   
    sequence.add(JPA_pulse_tomo, JPA_port, copy=False)   

    # sequence.add(Delay(400), digi_port, copy=False)   
    sequence.add(digi_acquire_tomo, digi_port, copy=False)  

    if draw_end == True:
        sequence.draw()
        raise SyntaxError
    
    return sequence

#phase relation check
print(lo_2pho.frequency() * 2 - lo_readout.frequency())

#Flux biases

#Current set!
current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()


current=100.8e-6

current_source.on()
current_source.ramp_current(current,5e-7,0.1)



#JPA amplification setup here!
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()

current_JPA=90.7e-6

JPA_current_source.on()
JPA_current_source.ramp_current(current_JPA,5e-7,0.1)


hvi_trigger.digitizer_delay(0)

# points_per_cycle = 10000
points_per_cycle = 1000
time = np.arange(points_per_cycle) * digi_ch.sampling_interval()

data = DataDict(
        time=dict(unit="ns"),
        waveform=dict(axes=["time"], unit="V"),
        wave_I=dict(axes=["time"], unit="V"),
        wave_Q=dict(axes=["time"], unit="V"),
        g_plus_e_I=dict(axes=["time"], unit="V"),
        g_minus_e_I=dict(axes=["time"], unit="V"),
        g_plus_e_Q=dict(axes=["time"], unit="V"),
        g_minus_e_Q=dict(axes=["time"], unit="V"),
    )


data.validate()

#In cases where more than 60000 cycles are needed, repeat the measurements with this!
# extra_reps = 500
extra_reps = 50

with DDH5Writer(data, data_path, name=measurement_name) as writer:
    writer.add_tag(tags)
    writer.backup_file([__file__, setup_file])
    writer.save_text("wiring.md", wiring)
    writer.save_dict("station_snapshot.json", station.snapshot())

    # for update_command in tqdm(variables.update_command_list):         
    g_plus_e_I=[]
    g_plus_e_Q=[]
    g_minus_e_I=[]
    g_minus_e_Q=[]

    for _ in  tqdm(range(extra_reps)):
        for state in ["0+1_i", "0+1_q", "0-1_i", "0-1_q"]:
            awg_1.flush_waveform()
            awg_2.flush_waveform()
            if state=="0-1_i":
                seq = photon_sequence(virtualz=True, phase=0)
            if state=="0-1_q":
                seq = photon_sequence(virtualz=True, phase= np.pi)
            if state=="0+1_i":
                seq = photon_sequence(virtualz=False, phase=0 * np.pi)
            if state=="0+1_q":
                seq = photon_sequence(virtualz=False, phase= np.pi)

            load_sequence2(seq, cycles=40000)
            data = run2(seq, plot = 0, JPA_TD = True).mean(axis=0) * voltage_step
            if state=="0+1_i": g_plus_e_I = np.append(g_plus_e_I, data)
            if state=="0+1_q": g_plus_e_Q = np.append(g_plus_e_Q, data)
            if state=="0-1_i": g_minus_e_I = np.append(g_minus_e_I, data)
            if state=="0-1_q": g_minus_e_Q = np.append(g_minus_e_Q, data)
    
    
    g_plus_e_I = g_plus_e_I.reshape(int(extra_reps), int(digi_ch.points_per_cycle())).mean(axis=0)
    g_plus_e_Q = g_plus_e_Q.reshape(int(extra_reps), int(digi_ch.points_per_cycle())).mean(axis=0)
    g_minus_e_I = g_minus_e_I.reshape(int(extra_reps), int(digi_ch.points_per_cycle())).mean(axis=0)
    g_minus_e_Q = g_minus_e_Q.reshape(int(extra_reps), int(digi_ch.points_per_cycle())).mean(axis=0)
    waveform_I = (g_plus_e_I - g_minus_e_I) / 2
    waveform_Q = (g_plus_e_Q - g_minus_e_Q) / 2
    waveform = (waveform_I + waveform_Q) / 2
    
    
    # digi_ch.delay(0)
    # digi_ch.points_per_cycle(points_per_cycle)


    writer.add_data(
                time=np.arange(len(waveform)) * digi_ch.sampling_interval(),
                waveform=waveform,
                wave_I = waveform_I,
                wave_Q = waveform_Q,
                g_plus_e_I=g_plus_e_I,
                g_minus_e_I=g_minus_e_I,
                g_plus_e_Q=g_plus_e_Q,
                g_minus_e_Q=g_minus_e_Q,
            )


current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()
print('finished')