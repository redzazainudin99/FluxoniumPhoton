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

delay = Variable("delay",50 * np.arange(50), "ns")
# duration = Variable("duration",[10,90,100,170], "ns")
variables = Variables([delay])

detuning = 0.002


seq = Sequence(port_list=[ge_drive_port, readout_port, digi_port])
seq.add(SetDetuning(detuning), ge_drive_port)
seq.call(ge_flat_halfpi_seq)
seq.add(Delay(delay), ge_drive_port)
seq.add(VirtualZ(np.pi), ge_drive_port)
seq.call(ge_half_pi_seq)
seq.add(VirtualZ(np.pi), ge_drive_port)
seq.trigger([ge_drive_port, readout_port, digi_port])
seq.call(readout_seq_JPA)


# sequence.draw()
# raise SystemError

data = DataDict(
    delay=dict(unit="ns"),
    s11=dict(axes=["delay"])
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


try:
    with DDH5Writer(data, data_path, name=measurement_name) as writer:
        writer.add_tag(tags)
        writer.add_tag(measurement_name)
        writer.backup_file([__file__, setup_file])
        writer.save_text("wiring.md", wiring)
        writer.save_dict("station_snapshot.json", station.snapshot())
        digi_ch.delay(0)
        for update_command in tqdm(variables.update_command_list):             
            seq.update_variables(update_command)
            load_sequence2(seq, cycles=40000)
            data = run2(seq, plot=0,JPA_TD = True).mean(axis=0)
            writer.add_data(
                delay = seq.variable_dict["delay"][0].value,
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