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

JPA_port.if_freq = JPA_port.if_freq #+ 0.006



def photon_sequence (virtualz, draw_end = False):
    
    sequence = Sequence([ge_drive_port,gf_drive_port, JPA_port, digi_port])
    sequence.add(Delay(500), ge_drive_port, copy=False)   
    if virtualz ==True:
        sequence.add(VirtualZ(np.pi), ge_drive_port,copy = False)
    sequence.call(ge_flat_halfpi_seq)
    if virtualz ==True:
        sequence.add(VirtualZ(-np.pi), ge_drive_port,copy = False)
    sequence.trigger([ge_drive_port,gf_drive_port,])
    sequence.call(gf_pi_seq)

    sequence.add(Delay(400), digi_port, copy=False)   
    sequence.add(digi_acquire, digi_port, copy=False)  

    if draw_end == True:
        sequence.draw()
        raise SyntaxError
    
    return sequence

# seq = photon_sequence(virtualz=True, phase = 0, draw_end = True)

drive_pulse_duration = 20000

JPA_pulse.params['duration'] = drive_pulse_duration + 3000
digi_acquire.params['duration'] = drive_pulse_duration + 3000

####GF PULSE PARAMS###
gf_pi.params['amplitude'] = 1.2
gf_pi_flat.params['top_duration'] = drive_pulse_duration

# gf_freq = 2.8
# gf_drive_port.if_freq = (gf_freq - gf_lo_freq)

# gf_freqs =  np.linspace(gf_lo_freq - 0.29, gf_lo_freq + 0.29,51)
# gf_freqs =  np.linspace(gf_freq - 0.1, gf_freq + 0.1,21)
gf_freqs =  [gf_freq]
# print(gf_freqs)
# gf_freqs =  [gf_freq]
# lo_2pho.frequency((gf_freq + gf_if_freq)*1e9)

#phase relation check
print(lo_2pho.frequency() * 2 - lo_readout.frequency())

#Flux biases

#Current set!
current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()

current=28.88e-6

current_source.on()
current_source.ramp_current(current,5e-7,0.1)

#Low 01 frequency case! Directly drive qubit with AWG, and set ge_lo_freq to 0!
ge_lo_freq=0


#JPA amplification setup here!
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()

current_JPA=-94.8e-6

JPA_current_source.on()
JPA_current_source.ramp_current(current_JPA,5e-7,0.1)


hvi_trigger.digitizer_delay(0)

points_per_cycle = 10000
time = np.arange(points_per_cycle) * digi_ch.sampling_interval()

data = DataDict(
        emission_frequency=dict(unit="GHz"),
        time=dict(unit="ns"),
        waveform=dict(axes=["emission_frequency", "time"], unit="V"),
        g_plus_e=dict(axes=["emission_frequency", "time"], unit="V"),
        g_minus_e=dict(axes=["emission_frequency", "time"], unit="V"),
    )


data.validate()

#In cases where more than 60000 cycles are needed, repeat the measurements with this!
# extra_reps = 4000
extra_reps = 100

with DDH5Writer(data, data_path, name=measurement_name) as writer:
    writer.add_tag(tags)
    writer.backup_file([__file__, setup_file])
    writer.save_text("wiring.md", wiring)
    writer.save_dict("station_snapshot.json", station.snapshot())

    for f in tqdm(gf_freqs):
        gf_drive_port.if_freq = f -gf_lo_freq
        g_plus_e = []
        g_minus_e = []

        for _ in  tqdm(range(extra_reps)):
            for state in ["0+1", "0-1"]:
                awg_1.flush_waveform()
                awg_2.flush_waveform()
                if state=="0-1":
                    seq = photon_sequence(virtualz=True)
                if state=="0+1":
                    seq = photon_sequence(virtualz=False)
                load_sequence2(seq, cycles=40000)
                data = run2(seq, plot = 0, JPA_TD = False).mean(axis=0) * voltage_step
                if state=="0+1": g_plus_e = np.append(g_plus_e, data)
                if state=="0-1": g_minus_e = np.append(g_minus_e, data)
        
        
        g_plus_e = g_plus_e.reshape(int(extra_reps), int(digi_ch.points_per_cycle())).mean(axis=0)
        g_minus_e = g_minus_e.reshape(int(extra_reps), int(digi_ch.points_per_cycle())).mean(axis=0)

        waveform = (g_plus_e - g_minus_e) / 2

        
        
        # digi_ch.delay(0)
        # digi_ch.points_per_cycle(points_per_cycle)


        writer.add_data(
                    emission_frequency=f,
                    time=np.arange(len(waveform)) * digi_ch.sampling_interval(),
                    waveform=waveform,
                    g_plus_e=g_plus_e,
                    g_minus_e=g_minus_e,
                )


current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()
print('finished')