import os

import matplotlib.pyplot as plt
import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer
from sequence_parser import Sequence, Variable, Variables
from tqdm import tqdm

from setup_td import *

measurement_name = os.path.basename(__file__)[:-3]

frequency = np.linspace(0.2, 0.4,5) #GHz
# frequency = np.linspace(0.45, 0.65, 101) #GHz

amp_vals = np.linspace(0.,0.5,2)
amplitude = Variable("amplitude", amp_vals, "V")
print(digi_ch.sampling_interval())


variables = Variables([amplitude])

sequence = Sequence([readout_port, ge_drive_port, digi_port, JPA_port])
sequence.trigger(all_ports)
sequence.add(Square(amplitude=amplitude, duration=1000), ge_drive_port, copy = False)
sequence.trigger(all_ports)
sequence.call(readout_seq_JPA)


# check_sequence(sequence, variables, idxlist=[1,-1])
# raise SystemError

#Current set!
current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()

current=100.8e-6

current_source.on()
current_source.ramp_current(current,5e-7,0.1)

#Low 01 frequency case! Directly drive qubit with AWG, and set ge_lo_freq to 0!
ge_lo_freq=0


#Continuous JPA amplification setup here!
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()

current_JPA=90.7e-6

JPA_current_source.on()
JPA_current_source.ramp_current(current_JPA,5e-7,0.1)


data = DataDict(
    frequency=dict(unit="GHz"),
    amplitude=dict(unit="V"),
    s11=dict(axes=["frequency", "amplitude"]),
)
data.validate()

with DDH5Writer(data, data_path, name=measurement_name) as writer:
    writer.add_tag(tags)
    writer.backup_file([__file__, setup_file])
    writer.save_text("wiring.md", wiring)
    writer.save_dict("station_snapshot.json", station.snapshot())
    for update_command in tqdm(variables.update_command_list):
        sequence.update_variables(update_command)
        for f in tqdm(frequency, leave=False):  
            # ge_drive_port.if_freq = (f - ge_lo_freq) 
            ge_drive_port.if_freq = f
            load_sequence2(sequence, cycles=30000)
            writer.add_data(
                frequency=f,
                amplitude=sequence.variable_dict["amplitude"][0].value,
                s11=demodulate(run2(sequence,  plot=0,JPA_TD = True).mean(axis=0)),
            )

current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()
