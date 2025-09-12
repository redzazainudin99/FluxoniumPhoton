import os

import matplotlib.pyplot as plt
import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer
from sequence_parser import Sequence, Variable, Variables
from tqdm import tqdm
import qcodes as qc
import qcodes.utils.validators as vals

from setup_td import *

# shot_count = 5000 + 1000*np.arange(30)
shot_count = 10000
repetition = 3


# hvi_trigger.digitizer_delay(400)
# hvi_trigger.trigger_period(100000)

measurement_name = os.path.basename(__file__)[:-3]


sequence_g_JPA  = Sequence([readout_port, digi_port, JPA_port])
# sequence_g_JPA.add(Delay(ge_flat_pi.params['duration']), readout_port, copy = False) 
sequence_g_JPA.trigger([readout_port, ge_drive_port, digi_port, JPA_port])
sequence_g_JPA.call(readout_seq_JPA)

sequence_e_JPA  = Sequence([readout_port, ge_drive_port, digi_port, JPA_port])
sequence_e_JPA.call(ge_flat_seq)
sequence_e_JPA.trigger([readout_port, ge_drive_port, digi_port, JPA_port])
sequence_e_JPA.call(readout_seq_JPA)



# sequence_g_JPA.draw()
# sequence_e_JPA.draw()
# raise SystemError

#Current set!
current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()

current=100.8e-6

current_source.on()
current_source.ramp_current(current,5e-7,0.1)

JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()

current_JPA=90.7e-6

JPA_current_source.on()
JPA_current_source.ramp_current(current_JPA,5e-7,0.1)


data = DataDict(
    shot=dict(),
    iq_g=dict(axes=["shot"]),
    iq_g_mean = dict(axes=["shot"]),
    iq_e=dict(axes=["shot"]),
    iq_e_mean = dict(axes=["shot"]),
)
data.validate()

try:
    with DDH5Writer(data, data_path, name=measurement_name) as writer:
        writer.add_tag(tags)
        writer.backup_file([__file__, setup_file])
        writer.save_text("wiring.md", wiring)
        writer.save_dict("station_snapshot.json", station.snapshot())


        load_sequence2(sequence_e_JPA,shot_count)
        data_e = run2(sequence_e_JPA,JPA_TD = True)
        s11_e = demodulate(data_e)
        s11_e_mean = demodulate(data_e.mean(axis = 0))

        load_sequence2(sequence_g_JPA,shot_count)
        data_g = run2(sequence_g_JPA,JPA_TD=True)
        s11_g = demodulate(data_g)
        s11_g_mean = demodulate(data_g.mean(axis = 0))

        writer.add_data(
                shot=np.arange(shot_count),
                iq_e=s11_e,
                iq_e_mean = s11_e_mean,
                iq_g = s11_g,
                iq_g_mean = s11_g_mean,
                )

        IQ_plot(
            demod_data = [s11_g,s11_e],#,s11_plus],
            tags = ['g state','e state'],# 'g+e superposition'],
            title = 'g vs e',
            writer = writer
            )
        


                


        # load_sequence2(sequence_plus, cycles=shot_count)
        # data_plus = run2(sequence_plus, plot = 0)/1000
        # s11_plus = demodulate(data_plus)
        # # s11_plus_mean = demodulate(data_plus.mean(axis = 0))
        # print('plus_done')

        
finally: 
    # off()
    print('finished')



