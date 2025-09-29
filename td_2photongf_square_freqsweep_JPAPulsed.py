import os

import matplotlib.pyplot as plt
import numpy as np
import qcodes as qc
import qcodes.utils.validators as vals
from sequence_parser import Sequence, Variable, Variables
from tqdm import tqdm

from setup_td import *

with open(__file__) as file:
    script = file.read()

measurement_name = os.path.basename(__file__)

freq_vals = np.linspace(gf_lo_freq - 0.29, gf_lo_freq + 0.29,51) #GHz
# freq_vals = np.linspace(0.1,0.3,2)

delay = 7000

# sequence = Sequence([readout_port, ge_drive_port, JPA_port, digi_port])
# # sequence.trigger([readout_port, ge_drive_port,JPA_port, digi_port])
# sequence.add(Square(amplitude=0.5,duration= 8000),ge_drive_port,copy=False)
# sequence.trigger([readout_port, ge_drive_port, digi_port,JPA_port])
# # sequence.add(Square(amplitude=1., duration=15000), JPA_port)
# sequence.call(JPA_square_seq)
# sequence.call(readout_seq)
# # sequence.add(Delay(duration= delay), readout_port)

sequence = Sequence([readout_port, gf_drive_port, JPA_port, digi_port])
# sequence.trigger([readout_port, ge_drive_port,JPA_port, digi_port])
sequence.add(Square(amplitude=0.8,duration= 3000),gf_drive_port,copy=False)
sequence.trigger([readout_port, gf_drive_port, digi_port,JPA_port])
# sequence.add(Square(amplitude=1., duration=15000), JPA_port)
# sequence.call(JPA_square_seq)
sequence.call(readout_seq_JPA)
# sequence.add(Delay(duration= delay), readout_port)

# sequence.draw()
# raise SystemError

data = DataDict(
    frequency=dict(unit="GHz"),
    s11=dict(axes=["frequency"])
)
data.validate()

# sequence.draw()
# raise SystemError

#Current set!
current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()

current=28.88e-6

current_source.on()
current_source.ramp_current(current,5e-7,0.1)

#Low 01 frequency case! Directly drive qubit with AWG, and set ge_lo_freq to 0!
ge_lo_freq=0


#Continuous JPA amplification setup here!
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()

current_JPA=-94.8e-6

JPA_current_source.on()
JPA_current_source.ramp_current(current_JPA,5e-7,0.1)

#JPA LO setup

# lo_JPA = N51xx('lo_JPA', 'TCPIP0::192.168.100.9::inst0::INSTR')
# lo_JPA = E82x7('lo_JPA', 'TCPIP0::192.168.100.7::inst0::INSTR')
# lo_JPA.power(-5.5)
# print(readout_if_freq)
# lo_JPA.frequency(readout_freq*2*1e9)
# station.add_component(lo_JPA)
# lo_JPA.output(False)
# lo_JPA.output(True)
# gf_drive_port.if_freq = 0.124 

try:
    with DDH5Writer(data, data_path, name=measurement_name) as writer:
        writer.add_tag(tags)
        writer.add_tag(measurement_name)
        writer.backup_file([__file__, setup_file])
        writer.save_text("wiring.md", wiring)
        writer.save_dict("station_snapshot.json", station.snapshot())
        digi_ch.delay(0)
        for f in tqdm(freq_vals):         
            gf_drive_port.if_freq = (f - gf_lo_freq) 
            # lo_2pho.frequency((f + gf_if_freq)*1e9)
            # print(ge_drive_port.if_freq)
            load_sequence2(sequence, cycles=20000)
            data = run2(sequence, plot=0,JPA_TD = True).mean(axis=0)
            writer.add_data(
                frequency = f,
                s11 = demodulate(data),
            )
            

            # IQ_plot(demod_data = [demodulate(run2(sequence, plot=0,JPA_TD = True))],#,s11_plus],
            # tags = ['s11'],# 'g+e superposition'],
            # title = 'Squeeze check!',
            # writer = writer
            # )
finally:
    current_source.ramp_current(0, step=5e-7, delay=0)
    current_source.off()

    JPA_current_source.ramp_current(0, step=5e-7, delay=0)
    JPA_current_source.off()
    # lo_JPA.output(False)

    print("finished")