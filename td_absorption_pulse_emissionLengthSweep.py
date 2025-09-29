import os

import matplotlib.pyplot as plt
import numpy as np
import qcodes as qc
import qcodes.utils.validators as vals
from sequence_parser import Sequence, Variable, Variables
from tqdm import tqdm

from setup_td import *
from photon_waveform_converter import *


with open(__file__) as file:
    script = file.read()

measurement_name = os.path.basename(__file__)

delay = Variable("delay", 10*np.arange(300) + 10, "ns")
# duration = Variable("duration", 100*np.arange(30) + 10, "ns")
variables = Variables([delay])


gf_pi_flat.params['top_duration'] = len(reversed_photon)

###################
sequence = Sequence([readout_port, gf_drive_port,ge_drive_port, JPA_port, digi_port])

#1 state initialization
sequence.call(ge_flat_seq)
sequence.trigger([readout_port, gf_drive_port,ge_drive_port, digi_port,JPA_port])

#weak coherent pulse drive      #Acquire acts as a placeholder for an arbitrary array!
sequence.add(ReverseExp(amplitude = amplitude, duration=1200), readout_port,copy=False)
#absorption pulse
sequence.add(Delay(duration = delay), gf_drive_port, copy= False )  
sequence.call(gf_pi_seq)

#readout
sequence.trigger([readout_port, gf_drive_port, ge_drive_port,digi_port,JPA_port])
sequence.call(readout_seq_JPA)

check_sequence(sequence, variables, idxlist=[1,-1])
# sequence.draw()
# raise SyntaxError





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


data = DataDict(
        absorption_delay=dict(unit="ns"),
        # pulse_duration = dict(unit = 'ns'),
        s11= dict(axes=["absorption_delay"])
    )

data.validate()


with DDH5Writer(data, data_path, name=measurement_name) as writer:
    writer.add_tag(tags)
    writer.backup_file([__file__, setup_file])
    writer.save_text("wiring.md", wiring)
    writer.save_dict("station_snapshot.json", station.snapshot())
    for update_command in tqdm(variables.update_command_list):
        sequence.update_variables(update_command)
        load_sequence_append( reversed_photon,readout_port,sequence, cycles=40000)
        writer.add_data(
            absorption_delay = sequence.variable_dict["delay"][0].value,
            # pulse_duration=sequence.variable_dict["duration"][0].value,
            s11=demodulate(run2(sequence,JPA_TD=True).mean(axis=0)),
        )

current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()
