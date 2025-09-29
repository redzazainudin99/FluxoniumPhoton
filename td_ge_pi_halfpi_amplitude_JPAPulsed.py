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

amplitude_vals = np.linspace(0,0.8,41)
amplitude = Variable("amplitude",amplitude_vals, "V")
variables = Variables([amplitude])


sequence_g = Sequence([readout_port, ge_drive_port, JPA_port, digi_port])
sequence_g.trigger([readout_port, ge_drive_port,JPA_port ,digi_port])
sequence_g.call(readout_seq_JPA)


ge_halfpi.params["amplitude"] = amplitude

sequence_half = Sequence([readout_port, ge_drive_port, JPA_port, digi_port])
for _ in range(1):
    sequence_half.call(ge_flat_halfpi_seq)
sequence_half.trigger([readout_port, ge_drive_port,JPA_port ,digi_port])
sequence_half.call(readout_seq_JPA)


sequence_e = Sequence([readout_port, ge_drive_port, JPA_port, digi_port])
for _ in range(1):
    sequence_half.call(ge_flat_seq)
sequence_half.trigger([readout_port, ge_drive_port,JPA_port ,digi_port])
sequence_half.call(readout_seq_JPA)

# check_sequence(sequence_pi, variables, idxlist=[1,-1])
# check_sequence(sequence_half, variables, idxlist=[1,-1])
# raise SystemError

#Current set!
current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()

current=28.88e-6

current_source.on()
current_source.ramp_current(current,5e-7,0.1)


#Continuous JPA amplification setup here!
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()

current_JPA=-94.8e-6

JPA_current_source.on()
JPA_current_source.ramp_current(current_JPA,5e-7,0.1)



data = DataDict(
    amplitude=dict(unit="V"),
    s11_g=dict(axes=["amplitude"]),
    s11_half=dict(axes=["amplitude"]),
    s11_e=dict(axes=["amplitude"]),
    mag_ratio = dict(axes = ['amplitude']),
    )
data.validate() 

try:
    with DDH5Writer(data, data_path, name=measurement_name) as writer:
        writer.add_tag(tags)
        writer.add_tag(measurement_name)
        writer.backup_file([__file__, setup_file])
        writer.save_text("wiring.md", wiring)
        writer.save_dict("station_snapshot.json", station.snapshot())
        for update_command in tqdm(variables.update_command_list):         
            # sequence_g.update_variables(update_command)
            load_sequence2(sequence_g, cycles=1000)
            data_g = run2(sequence_g, JPA_TD=True).mean(axis=0)
            s11_g = demodulate(data_g)

            sequence_half.update_variables(update_command)
            load_sequence2(sequence_half, cycles=1000)
            data_half = run2(sequence_half, JPA_TD=True).mean(axis=0)
            s11_half = demodulate(data_half)

            load_sequence2(sequence_e, cycles=1000)
            data_e = run2(sequence_e, JPA_TD=True).mean(axis=0)
            s11_e = demodulate(data_e)

            writer.add_data(
                amplitude =  sequence_g.variable_dict["amplitude"][0].value,
                s11_g = s11_g,
                s11_half = s11_half,
                s11_e = s11_e,
                mag_ratio = s11_half / (s11_g - s11_e)
            )

            # IQ_plot(
            #     demod_data = [s11],#,s11_g_JPA],#,s11_plus],
            #     tags = ['points'],#,'g state with JPA'],# 'g+e superposition'],
            #     title = 'Rabi oscillations in IQ',
            #     writer = writer
            #     )
finally:

    current_source.ramp_current(0, step=5e-7, delay=0)
    current_source.off()

    JPA_current_source.ramp_current(0, step=5e-7, delay=0)
    JPA_current_source.off()
    
    # lo_JPA.output(False)
    print("finished")