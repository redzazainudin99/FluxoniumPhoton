import os

import matplotlib.pyplot as plt
import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer
from sequence_parser import Sequence, Variable, Variables
from tqdm import tqdm
from plottr.data.datadict_storage import search_datadict
from setup_td import *
from tomography_modeFunctionPrep import mode_function





measurement_name = os.path.basename(__file__)[:-3]

shot_count = 10000
# repetition = 3

def photon_sequence_resetted_wScaling(init_state, phase, draw_end = False):
    sequence = Sequence([ge_drive_port,gf_drive_port, JPA_port, digi_port])

    #reset pulse resets to 1 state
    sequence.add(Square(amplitude=gf_pi.params['amplitude'], duration=5000), gf_drive_port, copy = False)   #reset pulse
    sequence.add(Delay(100), digi_port, copy=False)
    #Measure first
    sequence.trigger([ge_drive_port,gf_drive_port,JPA_port, digi_port])
    sequence.add(ResetPhase(phase = phase), JPA_port,copy = True)   
    sequence.add(JPA_pulse2, JPA_port, copy=False)   
    sequence.add(digi_acquire2, digi_port, copy=False)  
    sequence.trigger([ge_drive_port,gf_drive_port,JPA_port, digi_port])
    #reset pulse resets to 1 state
    sequence.add(Square(amplitude=gf_pi.params['amplitude'], duration=5000), gf_drive_port, copy = False)   #reset pulse
    # print('Done')
    sequence.trigger([ge_drive_port,gf_drive_port,JPA_port, digi_port])
    #switches for initial states
    if init_state == '0':
        sequence.call(ge_flat_seq)
        sequence.trigger([ge_drive_port,gf_drive_port,JPA_port, digi_port])
        sequence.call(gf_pi_seq)


    if init_state == '1':
        sequence.add(Delay(duration= ge_flat_pi.params['top_duration'] + ge_pi.params['duration']), ge_drive_port, copy = False)
        sequence.trigger([ge_drive_port,gf_drive_port,JPA_port, digi_port])
        sequence.call(gf_pi_seq)


    if init_state == '0+1':
        sequence.call(ge_flat_halfpi_seq)
        sequence.trigger([ge_drive_port,gf_drive_port,JPA_port, digi_port])
        sequence.call(gf_pi_seq)


    if init_state == '0-1':
        sequence.add(VirtualZ(np.pi), ge_drive_port,copy = False)
        sequence.call(ge_flat_halfpi_seq)
        sequence.add(VirtualZ(-np.pi), ge_drive_port,copy = False)
        sequence.trigger([ge_drive_port,gf_drive_port,JPA_port, digi_port])
        sequence.call(gf_pi_seq)


    if init_state == '0+i1':
        sequence.add(VirtualZ(0.5 * np.pi), ge_drive_port,copy = False)
        sequence.call(ge_flat_halfpi_seq)
        sequence.add(VirtualZ(-0.5*np.pi), ge_drive_port,copy = False)

    if init_state == '0-i1':
        sequence.add(VirtualZ(-0.5 * np.pi), ge_drive_port,copy = False)
        sequence.call(ge_flat_halfpi_seq)
        sequence.add(VirtualZ(0.5*np.pi), ge_drive_port,copy = False)
        sequence.trigger([ge_drive_port,gf_drive_port,JPA_port, digi_port])
        sequence.call(gf_pi_seq)

    if init_state == 'vacuum':
        sequence.add(Delay(duration= ge_flat_pi.params['top_duration'] + ge_pi.params['duration']), ge_drive_port, copy = False)
        sequence.trigger([ge_drive_port,gf_drive_port,JPA_port, digi_port])
        sequence.add(Delay(duration= gf_pi.params['duration'] + gf_pi_flat.params['top_duration']), ge_drive_port, copy = False)

    sequence.trigger([ge_drive_port,gf_drive_port,JPA_port, digi_port])

    sequence.add(ResetPhase(phase = phase), JPA_port,copy = False)   
    sequence.add(JPA_pulse_tomo, JPA_port, copy=False)   
    sequence.add(digi_acquire_tomo, digi_port, copy=False)  

    sequence.trigger([ge_drive_port,gf_drive_port,JPA_port, digi_port])
    

    if draw_end == True:
        sequence.draw()
        raise SyntaxError
    
    return sequence

# photon_sequence_resetted_wScaling(init_state='0', phase=0, draw_end= True )

#phase relation check
print(lo_2pho.frequency() * 2 - lo_readout.frequency())


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
    p_0=dict(axes=["shot"]),
    p_0_vacuum=dict(axes=["shot"]),
    q_0 = dict(axes=["shot"]),
    q_0_vacuum = dict(axes=["shot"]),

    p_1=dict(axes=["shot"]),
    p_1_vacuum=dict(axes=["shot"]),
    q_1 = dict(axes=["shot"]),
    q_1_vacuum = dict(axes=["shot"]),

    p_0plus1=dict(axes=["shot"]),
    p_0plus1_vacuum=dict(axes=["shot"]),
    q_0plus1 = dict(axes=["shot"]),
    q_0plus1_vacuum = dict(axes=["shot"]),

    p_0minus1=dict(axes=["shot"]),
    p_0minus1_vacuum=dict(axes=["shot"]),
    q_0minus1 = dict(axes=["shot"]),
    q_0minus1_vacuum = dict(axes=["shot"]),

    p_0plusi=dict(axes=["shot"]),
    p_0plusi_vacuum=dict(axes=["shot"]),
    q_0plusi = dict(axes=["shot"]),
    q_0plusi_vacuum = dict(axes=["shot"]),

    p_0minusi=dict(axes=["shot"]),
    p_0minusi_vacuum=dict(axes=["shot"]),
    q_0minusi = dict(axes=["shot"]),
    q_0minusi_vacuum = dict(axes=["shot"]),

    p_allvac=dict(axes=["shot"]),
    p_allvac_vacuum=dict(axes=["shot"]),
    q_allvac = dict(axes=["shot"]),
    q_allvac_vacuum = dict(axes=["shot"]),
)

data.validate()

extra_reps = 3

try:
    with DDH5Writer(data, data_path, name=measurement_name) as writer:
        writer.add_tag(tags)
        writer.backup_file([__file__, setup_file])
        writer.save_text("wiring.md", wiring)
        writer.save_dict("station_snapshot.json", station.snapshot())


        for state in ['0','1','0+1','0-1','0+i1','0-i1', 'vacuum']:
            result_p = []
            result_q = []
            for _ in tqdm(range(extra_reps)):
                
                awg_1.flush_waveform()
                awg_2.flush_waveform()

                sequence_p = photon_sequence_resetted_wScaling(init_state=state, phase=0 )
                
                load_sequence2(sequence_p,shot_count)
                data_p = run2(sequence_p,JPA_TD = True) * voltage_step
                result_p = np.append(result_p, data_p)
                # print('Done_p')
                awg_1.flush_waveform()
                awg_2.flush_waveform()

                sequence_q = photon_sequence_resetted_wScaling(init_state=state, phase=np.pi )

                load_sequence2(sequence_q,shot_count)
                data_q = run2(sequence_q,JPA_TD = True) * voltage_step
                result_q = np.append(result_q, data_q)
                # print('Done_q')

                        
            result_q = result_q.reshape(int(extra_reps*shot_count), int(digi_ch.points_per_cycle()))
            result_p = result_p.reshape(int(extra_reps*shot_count), int(digi_ch.points_per_cycle()))

            #defining acquire windows
            windows = digi_port.measurement_windows

            photon_result_p = result_p[:,int((windows[1][0] - windows[0][0])/digi_ch.sampling_interval()) :int((windows[1][1] - windows[0][0])/digi_ch.sampling_interval())]
            vacuum_result_p = result_p[:,int((windows[0][0] - windows[0][0])/digi_ch.sampling_interval()) :int((windows[0][1] - windows[0][0])/digi_ch.sampling_interval())]
            photon_result_q = result_q[:,int((windows[1][0] - windows[0][0])/digi_ch.sampling_interval()) :int((windows[1][1] - windows[0][0])/digi_ch.sampling_interval())]
            vacuum_result_q = result_q[:,int((windows[0][0] - windows[0][0])/digi_ch.sampling_interval()) :int((windows[0][1] - windows[0][0])/digi_ch.sampling_interval())]

            photon_result_p = photon_result_p * mode_function
            vacuum_result_p = vacuum_result_p * mode_function
            photon_result_q = photon_result_q * mode_function
            vacuum_result_q = vacuum_result_q * mode_function

            a_photon_p = demodulate(photon_result_p, demodulation_if=readout_freq-readout_lo_freq)
            a_vacuum_p = demodulate(vacuum_result_p, demodulation_if=readout_freq-readout_lo_freq)
            a_photon_q = demodulate(photon_result_q, demodulation_if=readout_freq-readout_lo_freq)
            a_vacuum_q = demodulate(vacuum_result_q, demodulation_if=readout_freq-readout_lo_freq)


            #writing based on state
            if state == '0':
                    p_0=a_photon_p,
                    p_0_vacuum=a_vacuum_p,
                    q_0 = a_photon_q,
                    q_0_vacuum = a_vacuum_q,

            if state == '1':
                    p_1=a_photon_p,
                    p_1_vacuum=a_vacuum_p,
                    q_1 = a_photon_q,
                    q_1_vacuum = a_vacuum_q,

            if state == '0+1':
                    p_0plus1=a_photon_p,
                    p_0plus1_vacuum=a_vacuum_p,
                    q_0plus1 = a_photon_q,
                    q_0plus1_vacuum = a_vacuum_q,

            if state == '0-1':
                    p_0minus1=a_photon_p,
                    p_0minus1_vacuum=a_vacuum_p,
                    q_0minus1 = a_photon_q,
                    q_0minus1_vacuum = a_vacuum_q,
            
            if state == '0+i1':
                    p_0plusi=a_photon_p,
                    p_0plusi_vacuum=a_vacuum_p,
                    q_0plusi = a_photon_q,
                    q_0plusi_vacuum = a_vacuum_q,

            if state == '0-i1':
                    p_0minusi=a_photon_p,
                    p_0minusi_vacuum=a_vacuum_p,
                    q_0minusi = a_photon_q,
                    q_0minusi_vacuum = a_vacuum_q,
        
            if state == 'vacuum':
                    p_allvac=a_photon_p,
                    p_allvac_vacuum=a_vacuum_p,
                    q_allvac = a_photon_q,
                    q_allvac_vacuum = a_vacuum_q,

        writer.add_data(
                    shot=np.arange(shot_count),

                    p_0 = p_0,
                    p_0_vacuum = p_0_vacuum,
                    q_0 = q_0,
                    q_0_vacuum = q_0_vacuum,

                    p_1 = p_1,
                    p_1_vacuum = p_1_vacuum,
                    q_1 = q_1,
                    q_1_vacuum = q_1_vacuum,

                    p_0plus1 = p_0plus1,
                    p_0plus1_vacuum = p_0plus1_vacuum,
                    q_0plus1 = q_0plus1,
                    q_0plus1_vacuum = q_0plus1_vacuum,

                    p_0minus1 = p_0minus1,
                    p_0minus1_vacuum = p_0minus1_vacuum,
                    q_0minus1 = q_0minus1,
                    q_0minus1_vacuum = q_0minus1_vacuum,

                    p_0plusi = p_0plusi,
                    p_0plusi_vacuum = p_0plusi_vacuum,
                    q_0plusi = q_0plusi,
                    q_0plusi_vacuum = q_0plusi_vacuum,

                    p_0minusi = p_0minusi,
                    p_0minusi_vacuum = p_0minusi_vacuum,
                    q_0minusi = q_0minusi,
                    q_0minusi_vacuum = q_0minusi_vacuum,

                    p_allvac=p_allvac,
                    p_allvac_vacuum=p_allvac_vacuum,
                    q_allvac = q_allvac,
                    q_allvac_vacuum = q_allvac_vacuum,
                )
        
finally: 
    # off()
    print('finished')

