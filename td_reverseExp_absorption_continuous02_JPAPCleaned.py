#this is to check the time delay between the readout pulse and digitizer pulse

import os

import matplotlib.pyplot as plt
import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer

from sequence_parser import Sequence
from setup_td import *
from ReverseExpPulse import * 
# from setup_td_pulses import *

measurement_name = os.path.basename(__file__)[:-3]
readout_phase = ResetPhase(phase=0)
# readout_pulse = ReverseExp(amplitude=1, duration=15000)      
readout_pulse = Square(amplitude=1., duration=1500)
digi_acquire = Acquire(duration = 10000)         #pulse input into digiitizer
# readout_acquire = Acquire(duration=15000)


gf_pi_flat.params['top_duration'] = 150000


freq_vals =  np.linspace(gf_freq - 0.2, gf_freq + 0.2, 41)

JPA_pulse.params['duration'] = 4000
def absorb_sequence(phase):
    revExp_sequence = Sequence([readout_port, ge_drive_port, gf_drive_port, JPA_port, digi_port])
    revExp_sequence.trigger([readout_port,ge_drive_port, gf_drive_port,  JPA_port,  digi_port])
    revExp_sequence.call(ge_flat_seq)
    revExp_sequence.trigger([readout_port,ge_drive_port, gf_drive_port, JPA_port,   digi_port])
    revExp_sequence.call(gf_pi_seq)
    revExp_sequence.add(ReverseExp(amplitude=0.1, duration=2400),readout_port, copy=False )
    
    revExp_sequence.add(ResetPhase(phase = phase), JPA_port,copy = False)   
    revExp_sequence.add(JPA_pulse, JPA_port, copy=False)   
    revExp_sequence.add(digi_acquire, digi_port, copy=False)                             #this is the digiitizer input, which is the reflected readout pulse
    revExp_sequence.trigger([readout_port,  ge_drive_port, gf_drive_port,  JPA_port, digi_port])
    revExp_sequence.add(Delay(10), readout_port)

    return revExp_sequence
# readout_pulse.params["amplitude"] = 1



# sequence.draw()
# raise SystemError
# plt.plot(readout_port.waveform.real)
# plt.show()
# raise SyntaxError
# lo_readout.power(20)
hvi_trigger.digitizer_delay(0)

points_per_cycle = 5000
time = np.arange(points_per_cycle) * digi_ch.sampling_interval()

data = DataDict(
    time=dict(unit="ns"),
    frequency = dict(unit= 'GHz'),
    waveform=dict(axes=["frequency", "time"], unit="V"),
    wave_I=dict(axes=["frequency", "time"], unit="V"),
    wave_Q=dict(axes=["frequency", "time"], unit="V"),
    )

data.validate()



#In cases where more than 60000 cycles are needed, repeat the measurements with this!
extra_reps = 10


with DDH5Writer(data, data_path, name=measurement_name) as writer:
    writer.add_tag(tags)
    writer.backup_file([__file__, setup_file])
    writer.save_text("wiring.md", wiring)
    writer.save_dict("station_snapshot.json", station.snapshot())
    for f in tqdm(freq_vals): 
            gf_drive_port.if_freq = f - gf_lo_freq  
            voltage_I = []
            voltage_Q = []

            for _ in tqdm(range(extra_reps)):
                for phase in [0, 2*np.pi]:
                    awg_1.flush_waveform()
                    awg_2.flush_waveform()
                    seq = absorb_sequence(phase)
                    load_sequence2(seq, cycles=40000)
                    data = run2(seq, plot = 0, JPA_TD = True).mean(axis=0) * voltage_step
                    if phase == 0 : voltage_I = np.append(voltage_I, data)
                    if phase == 2 * np.pi : voltage_Q = np.append(voltage_Q, data)

            voltage_I = voltage_I.reshape(int(extra_reps), int(digi_ch.points_per_cycle())).mean(axis=0)
            voltage_Q = voltage_Q.reshape(int(extra_reps), int(digi_ch.points_per_cycle())).mean(axis=0)
            waveform = (voltage_I + voltage_Q) / 2



            writer.add_data(
                time=time,
                frequency = f,
                wave_I = voltage_I,
                wave_Q = voltage_Q,
                waveform = waveform

            )


current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()
print('finished')