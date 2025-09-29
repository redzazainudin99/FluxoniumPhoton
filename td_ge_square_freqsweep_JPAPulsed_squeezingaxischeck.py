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

freq_vals = np.linspace(0.2,0.3,100)
# freq_vals = np.linspace(0.1,0.3,2)

JPA_phases = [0,22.5,45, 67.5, 90]
phases = Variable("JPA_phase",JPA_phases, unit = 'degrees')

variables = Variables([phases])


sequence = Sequence([readout_port, ge_drive_port, JPA_port, digi_port])
sequence.add(Square(amplitude=0.5,duration= 10000),ge_drive_port,copy=False)
sequence.trigger([readout_port, ge_drive_port, digi_port,JPA_port])
sequence.add(ResetPhase(phases), JPA_port,copy = False)   
sequence.add(ResetPhase(0), readout_port,copy = False)                                    #resets phase of the pulse
sequence.add(readout_pulse, readout_port, copy=False)  
sequence.add(JPA_pulse, JPA_port, copy=False)                                    #this is the readout pulse
sequence.add(digi_acquire, digi_port, copy=False)                             #this is the digiitizer input, which is the reflected readout pulse
sequence.trigger([readout_port, digi_port, JPA_port])                                  #syncs the readout and digiitizer pulses
sequence.add(Delay(0), readout_port, copy = False)   


# sequence.draw()
# raise SystemError

data = DataDict(
    frequency=dict(unit="Hz"),
    JPA_phase = dict(unit = 'degrees'),
    s11 = dict(axes = ['frequency','JPA_phase']))

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


try:
    with DDH5Writer(data, data_path, name=measurement_name) as writer:
        writer.add_tag(tags)
        writer.add_tag(measurement_name)
        writer.backup_file([__file__, setup_file])
        writer.save_text("wiring.md", wiring)
        writer.save_dict("station_snapshot.json", station.snapshot())
        digi_ch.delay(0)
        for update_command in tqdm(variables.update_command_list):
            sequence.update_variables(update_command)
            for f in tqdm(freq_vals):         
                ge_drive_port.if_freq = f
                load_sequence2(sequence, cycles=20000)
                data = run2(sequence, plot=0,JPA_TD = True).mean(axis=0)
                writer.add_data(
                    frequency=f,
                    JPA_phase=sequence.variable_dict["JPA_phase"][0].value,
                    s11=demodulate(run2(sequence, plot=0).mean(axis=0)),
                )

                # if f == freq_vals[0]:
                #     IQ_plot(demod_data = [demodulate(run2(sequence, plot=0,JPA_TD = True))],
                #         tags = ['s11'],# 'g+e superposition'],
                #         title = 'Squeeze check!',
                #         writer = writer
                #         )

finally:
    current_source.ramp_current(0, step=5e-7, delay=0)
    current_source.off()

    JPA_current_source.ramp_current(0, step=5e-7, delay=0)
    JPA_current_source.off()
    # lo_JPA.output(False)

    print("finished")