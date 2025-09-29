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

duration = Variable("duration", 10*np.arange(200)+ 10, "ns")
# duration = Variable("duration",[10,90,100,170], "ns")
variables = Variables([duration])

ge_flat_pi.params["duration"] = duration
# ge_flat_pi.params["amplitude"] = 0

sequence = Sequence([readout_port, ge_drive_port, JPA_port, digi_port])
for _ in range(1):
    sequence.call(ge_flat_seq)
sequence.trigger([readout_port, ge_drive_port,JPA_port ,digi_port])
sequence.call(readout_seq_JPA)

# check_sequence(sequence, variables, idxlist=[1,-1])
# raise SystemError

#Current set!
current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()

current=101.3e-6

current_source.on()
current_source.ramp_current(current,5e-7,0.1)


#Continuous JPA amplification setup here!
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()

current_JPA=84e-6

JPA_current_source.on()
JPA_current_source.ramp_current(current_JPA,5e-7,0.1)



data = DataDict(
    duration=dict(unit="ns"),
    s11=dict(axes=["duration"])
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
            sequence.update_variables(update_command)
            load_sequence2(sequence, cycles=60000)
            data = run2(sequence, JPA_TD=True).mean(axis=0)
            s11 = demodulate(data)
            writer.add_data(
                duration = sequence.variable_dict["duration"][0].value,
                s11 = s11,
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