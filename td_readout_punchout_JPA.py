import os

import matplotlib.pyplot as plt
import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer
from sequence_parser import Sequence, Variable, Variables
from tqdm import tqdm

from setup_td import *

measurement_name = os.path.basename(__file__)[:-3]

frequency = np.linspace(5.3,  5.31, 51) #GHz
# frequency = np.linspace(5.25,  5.4, 10) #GHz

# amp_vals = np.linspace(0, 1.4, 11)
amp_vals = np.linspace(0.5, 1.4, 20)
amps = Variable("amps", amp_vals, "V")


variables = Variables([amps])

sequence = Sequence(all_ports)

sequence.trigger(all_ports)
sequence.add(ResetPhase(0), readout_port)   
sequence.add(Square(amplitude=amps,duration = 15000), readout_port, copy=False)
sequence.add(Acquire(duration =15000)  , digi_port, copy=False)   
sequence.trigger(all_ports)
sequence.add(Delay(25), readout_port, copy = False) 



# check_sequence(sequence, variables, idxlist=[1,-1])
# raise SystemError

#Current set!
current_source.ramp_current(0, step=5e-8, delay=0)
current_source.off()

current=28.88e-6


current_source.on()
current_source.ramp_current(current, 5e-8, delay=0)

#Continuous JPA amplification setup here!
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()

current_JPA=-94.8e-6

JPA_current_source.on()
JPA_current_source.ramp_current(current_JPA,5e-7,0.1)

#JPA LO setup

lo_JPA = N51xx('lo_JPA', 'TCPIP0::192.168.100.9::inst0::INSTR')
# lo_JPA = E82x7('lo_JPA', 'TCPIP0::192.168.100.7::inst0::INSTR')
lo_JPA.power(1)
# print(readout_if_freq)
lo_JPA.frequency(readout_freq*2*1e9)
# station.add_component(lo_JPA)
lo_JPA.output(True)


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
            # lo_readout.frequency((f - readout_if_freq)*1e9)
            readout_port.if_freq = ( readout_lo_freq -f ) 
            load_sequence2(sequence, cycles=1000)
            writer.add_data(
                frequency=f,
                amplitude=sequence.variable_dict["amps"][0].value,
                s11=demodulate(run2(sequence, plot=0).mean(axis=0)),
            )

current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()

lo_JPA.output(False)