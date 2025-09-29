#this is a general template for time domain measurements
import numpy as np
import matplotlib.pyplot as plt
import qcodes as qc
from plottr.data.datadict_storage import DataDict, DDH5Writer
from qcodes.instrument_drivers.rohde_schwarz.SGS100A import \
    RohdeSchwarz_SGS100A
from qcodes.instrument_drivers.yokogawa.GS200 import GS200
import os 
from qcodes_drivers.N51x1 import N51x1
from qcodes_drivers.E82x7 import E82x7
from qcodes_drivers.HVI_Trigger import HVI_Trigger
from qcodes_drivers.iq_corrector import IQCorrector
from qcodes_drivers.M3102A import M3102A
from qcodes_drivers.M3202A import M3202A
from sequence_parser import Port, Sequence
from sequence_parser.instruction import (Acquire, Delay, Gaussian, HalfDRAG,
                                         ResetPhase, Square)

import matplotlib.colors as   mcolors
# from ReverseExpPulse import * 
# from setup_td_pulses import *

from N51xx import N51xx

from sequence_parser import Port, Sequence
from sequence_parser.variable import Variable, Variables
from sequence_parser.instruction import *


######FOR LOGGING#####
setup_file = __file__
tags = ["TD", "CDK185", "CL5R"]
data_path = "D:\Redza\Logs"
wiring = "\n".join([
    """
    qubit drive
    M3202A_#6-1 - 500mm - 20 dBm - Iin#4
    M3202A_#6-2 - 500mm - 20 dBm - Qin#4
    N5173B - 1500mm - LO#4
    RFOut#4 - 1500mm - E4407B

    """
])

######END OF LOGGING#####






######DEFINING PULSE PARAMETERS#####

#readout parameters
electrical_delay = 42e-9  # sec
# readout_freq = 10.5165 # GHz

readout_freq = 5.307 # GHz
# readout_freq = 5.3809 # GHz
# readout_freq = 4.3364 # GHz
readout_lo_freq =readout_freq + 0.14 #GHz
readout_if_freq = readout_lo_freq - readout_freq 
###drive parameters

#ge transition parameters
ge_freq=0.2915  #GHz
ge_lo_freq = 0.0#GHz
ge_if_freq = ge_freq - ge_lo_freq
# ge_if_freq = 0.265

#ef transition parameters
ef_freq = 2.8071 #GHz
ef_lo_freq = ef_freq + 0.124 #GHz 
ef_if_freq = ef_freq - ef_lo_freq


#gf transition parameters
gf_freq = 2.7988 #GHz
# gf_lo_freq = gf_freq + 0.124 #GHz
gf_lo_freq = readout_lo_freq/2 
gf_if_freq = gf_freq - gf_lo_freq


#fh transition parameters
fh_freq = 8.1038
fh_lo_freq = 8 #GHz
fh_if_freq = fh_freq - fh_lo_freq

#JPA parameters
JPA_pump_freq = readout_freq * 2
# JPA_lo_freq = ( 5.307 + 0.08) * 2
JPA_lo_freq = ( readout_freq + readout_if_freq) * 2
JPA_if_freq = JPA_pump_freq - JPA_lo_freq


#listing out the ports
readout_port = Port("readout_port", if_freq = readout_if_freq, max_amp=1.5)
ge_drive_port = Port("ge_port",if_freq =  ge_if_freq, max_amp=1.5)
ef_drive_port = Port("ef_port",if_freq =  ef_if_freq, max_amp=1.5)
gf_drive_port = Port("gf_port", if_freq = gf_if_freq , max_amp=1.5)
fh_drive_port = Port("fh_port", if_freq = fh_if_freq , max_amp=1.5)
digi_port = Port("digi_port")
JPA_port = Port('JPA_port', if_freq = JPA_if_freq, max_amp = 1.5)

all_ports = [readout_port, ge_drive_port, ef_drive_port, gf_drive_port, fh_drive_port, digi_port, JPA_port]

######END OF PULSE PARAMETERS#####



######PULSE SEQUENCES#####

####readout pulse
#initializing pulse sequence
readout_seq = Sequence([readout_port, digi_port])                                  

#defining singular pulses
readout_pulse1 = Square(amplitude=0.46, duration= 15200)               #readout pulse
digi_acquire = Acquire(duration = readout_pulse1.params["duration"] )         #pulse input into digiitizer

#adding pulses to the sequence
# readout_seq.trigger([readout_port, digi_port])                                                  #trigger pulse syncs the pulses across the ports
readout_seq.add(ResetPhase(0), readout_port,copy = False)                                    #resets phase of the pulse
readout_seq.add(readout_pulse1, readout_port, copy=False)                                    #this is the readout pulse
readout_seq.add(digi_acquire, digi_port, copy=False)                             #this is the digiitizer input, which is the reflected readout pulse
readout_seq.trigger([readout_port, digi_port])                                  #syncs the readout and digiitizer pulses
readout_seq.add(Delay(0), readout_port, copy = False)                                        #adds a delay pulse for good measure

####readout pulse with JPA
#initializing pulse sequence
readout_seq_JPA = Sequence([readout_port, digi_port,JPA_port])                                  

#defining singular pulses
readout_pulse = Square(amplitude=0.1, duration= 15000)               #readout pulse
digi_acquire = Acquire(duration = readout_pulse.params["duration"] + 1000)         #pulse input into digiitizer 
JPA_phase = ResetPhase(phase =0.5* np.pi)
JPA_pulse = Square(amplitude=1.4, duration= 15000)    
  

#adding pulses to the sequence
# readout_seq.trigger([readout_port, digi_port])                                                  #trigger pulse syncs the pulses across the ports
# readout_seq_JPA.add(ResetPhase(45), JPA_port,copy = False)   
readout_seq_JPA.add(JPA_phase, JPA_port,copy = False)   
readout_seq_JPA.add(ResetPhase(0), readout_port,copy = False)                                    #resets phase of the pulse
readout_seq_JPA.add(readout_pulse, readout_port, copy=False)  
readout_seq_JPA.add(JPA_pulse, JPA_port, copy=False)                                    #this is the readout pulse
readout_seq_JPA.add(digi_acquire, digi_port, copy=False)                             #this is the digiitizer input, which is the reflected readout pulse
readout_seq_JPA.trigger([readout_port, digi_port, JPA_port])                                  #syncs the readout and digiitizer pulses
readout_seq_JPA.add(Delay(0), readout_port, copy = False)                                        #adds a delay pulse for good measure



#for tomography
digi_acquire_tomo = Acquire(duration = 1200)         #pulse input into digiitizer 
JPA_phase_tomo = ResetPhase(phase =0.5* np.pi)
JPA_pulse_tomo = Square(amplitude=1.1, duration= 1200)    

#for scaling measurements of the vacuum at the end of the tomography measurements
digi_acquire2 = Acquire(duration = 1200)   
JPA_pulse2 = Square(amplitude=1.1, duration= 1200) 


# ##GE pi pulse
# #initializing pulse sequence
# ge_pi_seq = Sequence([ge_drive_port])                                  

# #defining singular pulses
# ge_pi = Gaussian(amplitude=0.4, fwhm=10, duration=30, zero_end=True)    #standard pi pulse
# ge_pi_pulse_drag = HalfDRAG(ge_pi, beta=0)                            #correction with DRAG

# #adding pulses to the sequence
# ge_pi_seq.add(ge_pi_pulse_drag, ge_drive_port,copy=False)


#GE flat-top gaussian
ge_pi = Gaussian(amplitude=0.35, fwhm=20, duration=30, zero_end=True)    
#initializing pulse sequence
ge_flat_seq = Sequence([ge_drive_port])                                  

#defining singular pulses
# ge_flat_pi  = Square(amplitude=0.4, duration= 30)
ge_flat_pi  = FlatTop(ge_pi , top_duration= 100)      #standard pi pulse
# ge_flat_pulse_drag = HalfDRAG(ge_flat_pi, beta=0)                            #correction with DRAG

#adding pulses to the sequence
ge_flat_seq.add(ge_flat_pi, ge_drive_port,copy=False)



#GE flat-top gaussian half pi
#initializing pulse sequence
ge_halfpi =  Gaussian(amplitude= ge_pi.params['amplitude']/2 , fwhm=ge_pi.params['fwhm'], duration=ge_pi.params['duration'], zero_end=True) 
ge_flat_halfpi_seq = Sequence([ge_drive_port])                                  

#defining singular pulses
ge_flat_halfpi = FlatTop(ge_halfpi , top_duration= ge_flat_pi.params['top_duration'])  #standard pi pulse
# ge_flat_half_pulse_drag = HalfDRAG(ge_flat_halfpi, beta=0)                            #correction with DRAG

#adding pulses to the sequence
ge_flat_halfpi_seq.add(ge_flat_halfpi, ge_drive_port,copy=False)


#GE flat-top gaussian half pi
#initializing pulse sequence
ge_halfpi2 =  Gaussian(amplitude= ge_pi.params['amplitude'] , fwhm=ge_pi.params['fwhm'], duration=ge_pi.params['duration'], zero_end=True) 
ge_flat_halfpi_seq2 = Sequence([ge_drive_port])                                  

#defining singular pulses
ge_flat_halfpi2 = FlatTop(ge_halfpi2 , top_duration= 1500)  #standard pi pulse
# ge_flat_half_pulse_drag = HalfDRAG(ge_flat_halfpi, beta=0)                            #correction with DRAG

#adding pulses to the sequence
ge_flat_halfpi_seq2.add(ge_flat_halfpi2, ge_drive_port,copy=False)







# ##GE half pi
# #initializing pulse sequence
# ge_half_pi_seq = Sequence()                                  

# #defining singular pulses
# ge_half_pi = Gaussian(amplitude=ge_pi.params['amplitude']/2, fwhm=12, duration=40, zero_end=True)    #standard pi pulse
# ge_half_pi_pulse_drag = HalfDRAG(ge_half_pi, beta=-0.1404)                                           #correction with DRAG

# #adding pulses to the sequence
# ge_half_pi_seq.add(ge_half_pi_pulse_drag, ge_drive_port, copy=False)



##EF pi pulse
#initializing pulse sequence
ef_pi_seq = Sequence()                                  

#defining singular pulses
ef_pi = Gaussian(amplitude=0.82322, fwhm=12, duration=40, zero_end=True)    #standard pi pulse
ef_pi_pulse_drag = HalfDRAG(ef_pi, beta=-0.1404)                            #correction with DRAG

#adding pulses to the sequence
ef_pi_seq.add(ef_pi_pulse_drag, ef_drive_port, copy=False)



##EF half pi
#initializing pulse sequence
ef_half_pi_seq = Sequence()                                  

#defining singular pulses
ef_half_pi = Gaussian(amplitude=ef_pi.params['amplitude']/2, fwhm=12, duration=40, zero_end=True)    #standard pi pulse
ef_half_pi_pulse_drag = HalfDRAG(ef_half_pi, beta=-0.1404)                                           #correction with DRAG

#adding pulses to the sequence
ef_half_pi_seq.add(ef_half_pi_pulse_drag, ef_drive_port, copy=False)



##2-photon GF pi pulse
#initializing pulse sequence
gf_pi_seq = Sequence()                                  

#defining singular pulses
gf_pi = RaisedCos(amplitude=0.315, duration= 40)    #standard pi pulse
gf_pi_flat = FlatTop(gf_pi, top_duration = 3000)
# gf_pi_pulse_drag = HalfDRAG(gf_pi, beta=0)                            #correction with DRAG

#adding pulses to the sequence
gf_pi_seq.add(gf_pi_flat, gf_drive_port, copy=False)

##2-photon GF pi pulse 2 
#initializing pulse sequence
gf_pi_seq2 = Sequence()                                  

#defining singular pulses
gf_pi2 = RaisedCos(amplitude=1, duration= 2000)    #standard pi pulse
gf_pi_flat2 = FlatTop(gf_pi2, top_duration = 4000)
# gf_pi_pulse_drag = HalfDRAG(gf_pi, beta=0)                            #correction with DRAG

#adding pulses to the sequence
gf_pi_seq2.add(gf_pi_flat2, gf_drive_port, copy=False)




##JPA pulse
#initializing pulse sequence
JPA_square_seq = Sequence([JPA_port])

#defining singular pulses
#adding pulses to the sequence

JPA_square_seq.add(ResetPhase(0), JPA_port,copy = False)                                    #resets phase of the pulse
JPA_square_seq.add(Square(amplitude=0.7, duration= 15000), JPA_port, copy=False)        #this is the readout pulse
# JPA_square_seq.add(digi_acquire, digi_port, copy=False)                             #this is the digiitizer input, which is the reflected readout pulse



######END OF PULSE SEQUENCES#####








######PHYSICAL INSTRUMENT SETUP#####

station = qc.Station()      #initializing the setup class object
run_dict = {}               #dictionary for the run function later

#current source, in case a bias line is used
current_source = GS200("current_source", "TCPIP0::192.168.100.99::inst0::INSTR")
station.add_component(current_source)

JPA_current_source = GS200("current_source2", "TCPIP0::192.168.100.95::inst0::INSTR")
station.add_component(JPA_current_source)


#AWGs
awg_1 = M3202A('awg_readout', chassis=1, slot=8)    #initializing AWG object
awg_1.channels.stop()                        #stopping output of all channels
awg_1.flush_waveform()                       #deletes preloaded waveforms, and flushes AWG queues
station.add_component(awg_1)                 #adds AWG object to setup
#SSBs are being used here, meaning that only 1 AWG channel is needed for each LO
awg_readout = awg_1.ch1
# awg_JPA = awg_1.ch2
awg_2pho = awg_1.ch3
awg_qubit = awg_1.ch4

awg_2= M3202A('awg_JPA', chassis=1, slot=3)    #initializing AWG object
awg_2.channels.stop()                        #stopping output of all channels
awg_2.flush_waveform()                       #deletes preloaded waveforms, and flushes AWG queues
station.add_component(awg_2)                 #adds AWG object to setup

awg_2photon_I = awg_2.ch1
awg_2photon_Q = awg_2.ch2
awg_JPA_I = awg_2.ch3
awg_JPA_Q = awg_2.ch4


# awg_2 = M3202A('awg_fogi', chassis=1, slot=4)    #initializing AWG object
# awg_2.channels.stop()                        #stopping output of all channels
# awg_2.flush_waveform()                       #deletes preloaded waveforms, and flushes AWG queues
# station.add_component(awg_2)                 #adds AWG object to setup
# #AWG channels
# awg_readout = awg_2.ch2
# awg_fogi_I = awg_2.ch3
# awg_fogi_Q = awg_2.ch4



#HVI Trigger
hvi_trigger = HVI_Trigger('hvi_trigger', "PXI0::1::BACKPLANE")
station.add_component(hvi_trigger)
hvi_trigger.digitizer_delay(400)
hvi_trigger.trigger_period(100000) # ns


#digitizer 
digi = M3102A('digitizer', chassis=1, slot=10)
station.add_component(digi)
digi_ch = digi.ch4
digi_ch.high_impedance(False)  # 50 Ohms
digi_ch.half_range_50(0.5)  # V_pp / 2
digi_ch.ac_coupling(False)  # dc coupling
digi_ch.sampling_interval(2); sampling = digi_ch.sampling_interval()  # ns
digi_ch.trigger_mode("software/hvi")
digi_ch.timeout(10000)  # ms                                                           
voltage_step=digi_ch.half_range_50()/(2**15-1)

digi_ch.half_range_50(4.0)  # V_pp / 2
# dig_ch.sampling_interval(2)  # ns
# dig_ch.timeout(10000)  # ms                                                           
voltage_step=digi_ch.half_range_50()/(2**15-1)


# # # #Local Oscillators
# lo_drive = N51x1('lo_drive', 'TCPIP0::192.168.100.49::inst0::INSTR')
# lo_drive.power(6)


lo_2pho = N51x1('lo_2pho', 'TCPIP0::192.168.100.49::inst0::INSTR')
# lo_2pho.power(6)          #for ssb
lo_2pho.power(16)          #for iq mixer
lo_2pho.frequency(gf_lo_freq*1e9)
station.add_component(lo_2pho)

lo_readout = E82x7('lo_readout', 'TCPIP0::192.168.100.7::inst0::INSTR')
# lo_readout = N51xx('lo_readout', 'TCPIP0::192.168.100.9::inst0::INSTR')
# lo_readout.power(17)
lo_readout.power(20)
lo_readout.frequency(readout_lo_freq*1e9)
station.add_component(lo_readout)

# lo_JPA = E82x7('lo_JPA', 'TCPIP0::192.168.100.7::inst0::INSTR')
# lo_JPA.power(-5)
# lo_JPA.frequency(JPA_lo_freq * 1e9)
# station.add_component(lo_JPA)


# lo_fogi = N51x1('lo_fogi', 'TCPIP0::192.168.100.5::inst0::INSTR')
# lo_fogi.power(18)
# lo_fogi.frequency(ge_freq*1e9)
# station.add_component(lo_fogi)
###END OF PHYSICAL INSTRUMENT SETUP###

#If a JPA is used, setup here
# lo_JPA = N51xx('lo_drive', 'TCPIP0::192.168.100.9::inst0::INSTR')
# lo_JPA.power(9)
# lo_JPA.frequency(readout_freq*2*1e9)
# station.add_component(lo_JPA)


# ###IQ CALIBRATION###
#for each device using IQ mixers, this type of calibration is required

iq_corrector_JPA  = IQCorrector(
    awg_JPA_I,
    awg_JPA_Q,
    "D:\Redza\Logs\IQ_calibration",
    lo_leakage_datetime="2025-09-21T171611",
    rf_power_datetime="2025-09-21T172011",
    len_kernel=41,
    fit_weight=10,
    plot=False,
)
# plt.show()


iq_corrector_2photon = IQCorrector(
    awg_2photon_I,
    awg_2photon_Q,
    "D:\Redza\Logs\IQ_calibration",
    lo_leakage_datetime="2025-09-21T205956",
    rf_power_datetime="2025-09-21T210309",
    len_kernel=41,
    fit_weight=10,
    plot=False,
)
# plt.show()
###END OF IQ CALIBRATION###


#functions
#loader functions
#REMEMBER! When AWGs are flushed, all the ports of that AWG have their waveforms removed.
#SO! If you plan to use an AWG for more than one type of drive pulse, make sure the flushing
#of AWGs is only at the starting load sequence!

def readout_seq_load(readout_awg:M3202A, I_channel, readout_id , cycles:int):
    """loads a readout port sequence
        Args:
            readout_awg: The AWG performing the readout
            readout_id: ID for the readout waveform 
            I_channel: The channel of the AWG performing the readout pulse

    """
    readout_awg.stop_all()
    readout_awg.flush_waveform()
    readout_awg.load_waveform(readout_port.waveform.real, readout_id , append_zeros=True)
    I_channel.queue_waveform(readout_id, trigger="software/hvi", cycles=cycles)

def IQ_seq_load(iq_awg, iq_corrector, port, i_drive, q_drive, i_id, q_id, cycles):
    """loads an IQ pulse sequence
        Args:
            iq_awg: The AWG performing the pulse
            iq_corrector: corrector for the corresponding AWG
            port: which port corresponds to the IQ sequence
            i_drive: channel corresponding to the I drive on the AWG
            q_drive: channel corresponding to the Q drive on the AWG
            i_id:ID for the I waveform
            q_id:ID for the Q waveform

    """
    i, q = iq_corrector.correct(port.waveform)
    iq_awg.stop_all()
    iq_awg.flush_waveform()
    iq_awg.load_waveform(i, i_id, append_zeros=True)
    iq_awg.load_waveform(q, q_id, append_zeros=True)
    i_drive.queue_waveform(i_id, trigger="software/hvi", cycles=cycles)
    q_drive.queue_waveform(q_id, trigger="software/hvi", cycles=cycles)
    i_drive.dc_offset(iq_corrector.i_offset)
    q_drive.dc_offset(iq_corrector.q_offset)

def SSB_seq_load(ssb_awg, port, awg_drive, awg_id, cycles):
    """loads an SSB pulse sequence
        Args:
            ssb_awg: The AWG performing the pulse
            port: which port corresponds to the SSB sequence
            awg_drive: channel corresponding to the SSB drive on the AWG
            awg_id:ID for the SSB waveform

    """
    waveform = port.waveform.real
    ssb_awg.stop_all()
    # ssb_awg.flush_waveform()          
    ssb_awg.load_waveform(waveform, awg_id, append_zeros=True)
    awg_drive.queue_waveform(awg_id, trigger="software/hvi", cycles=cycles)


def digi_load(digi_ch, cycles):
    """loads the digitizer measurement sequence
        Args:
        digi_ch: channel of the digitizer
            cycles
    """
    acquire_start=digi_port.measurement_windows[0][0]
    acquire_end=digi_port.measurement_windows[-1][-1]
    digi_ch.delay(int(acquire_start//digi_ch.sampling_interval()))
    digi_ch.points_per_cycle(int((acquire_end-acquire_start)/digi_ch.sampling_interval()))
    assert digi_ch.points_per_cycle() % digi_ch.sampling_interval() == 0



def demodulate(data, demodulation_if = readout_if_freq):
    t = np.arange(data.shape[-1]) * digi_ch.sampling_interval()
    return (data * np.exp(2j * np.pi * demodulation_if * t)).mean(axis=-1)


def load_note(data_path, date, name):
    lines = []
    with open(f'{data_path}\\{date}\\{name}', encoding='utf-8') as f:
        lines = f.readlines()  
    return"".join(lines)

def error_print(e):
    print('type:' + str(type(e)))
    print('args:' + str(e.args))
    print('message:' + e.message)
    print('error:' + str(e))


#these are functions to load and run sequences

def load_sequence(sequence: Sequence, cycles: int):
    sequence.compile()
    if readout_port in sequence.port_list:
        readout_seq_load(awg_2, awg_readout , readout_id = 0,  cycles = cycles)
    if ge_drive_port in sequence.port_list:
        IQ_seq_load(awg_1, iq_corrector_drive, ge_drive_port, awg_qubit_I, awg_qubit_Q, i_id = 1, q_id = 2, cycles = cycles)
    if digi_port in sequence.port_list:
        digi_load(digi_ch, cycles = cycles)
    digi_ch.cycles(cycles)

def run(sequence:Sequence, plot=False, lo_on=True):
    hvi_trigger.output(False)
    assert digi_ch.trigger_mode()=="software/hvi"
    if readout_port in sequence.port_list:
        assert digi_ch.cycles()==awg_readout.cycles()[0], f'{digi_ch.cycles()}, {awg_readout.cycles()}'
        if lo_on:lo_readout.output(True)
        awg_readout.start()
    if ge_drive_port in sequence.port_list:
        assert digi_ch.cycles()==awg_qubit_I.cycles()[0], f'{digi_ch.cycles()}, {awg_qubit_I.cycles()}'
        if lo_on: lo_drive.output(True)
        awg_qubit_I.start()
        awg_qubit_Q.start()
    digi_ch.start()
    hvi_trigger.output(True)
    data = digi_ch.read()
    hvi_trigger.output(False)
    if plot:
        plt.plot(digi_ch.sampling_interval() * np.arange(len(data[0])), data.mean(axis=0) * voltage_step)
        plt.show()
    return data

#The previous functions were made with IQ calibrations in mind. The next ones are for when SSB mixers are used
def load_sequence_SSB(sequence: Sequence, cycles: int):
    sequence.compile()
    if readout_port in sequence.port_list:
        readout_seq_load(awg_1, awg_readout , readout_id = 0,  cycles = cycles)
    if ge_drive_port in sequence.port_list:
        SSB_seq_load(awg_1, ge_drive_port ,awg_qubit, awg_id=1, cycles= cycles )
    if digi_port in sequence.port_list:
        digi_load(digi_ch, cycles = cycles)
    digi_ch.cycles(cycles)

def run_SSB(sequence:Sequence, plot=False, lo_on=True):
    hvi_trigger.output(False)
    assert digi_ch.trigger_mode()=="software/hvi"
    if readout_port in sequence.port_list:
        assert digi_ch.cycles()==awg_readout.cycles()[0], f'{digi_ch.cycles()}, {awg_readout.cycles()}'
        if lo_on:lo_readout.output(True)
        awg_readout.start()
    if ge_drive_port in sequence.port_list:
        assert digi_ch.cycles()==awg_qubit.cycles()[0], f'{digi_ch.cycles()}, {awg_qubit.cycles()}'
        if lo_on: lo_drive.output(True)
        awg_qubit.start()

    digi_ch.start()
    hvi_trigger.output(True)
    data = digi_ch.read()
    hvi_trigger.output(False)
    if plot:
        plt.plot(digi_ch.sampling_interval() * np.arange(len(data[0])), data.mean(axis=0) * voltage_step)
        plt.show()
    return data

#Function for checking pulse sequences

def check_sequence(seq:Sequence, var:Variables, idxlist, port_list=all_ports):
    for ccc in range(len(idxlist)):
        idx=idxlist[ccc]
        update_command = var.update_command_list[idx]
        seq.update_variables(update_command)
        seq.draw()
        measurement_windows = seq.get_waveform_information()[digi_port.name]['measurement_windows']
        #print(f"measurement_windows :{measurement_windows}")
        print("measurement_windows :{measurement_windows}")
        # for port in port_list:
    #     plt.plot(port.waveform.real)
    # plt.show()
    raise SystemError


def load_sequence2(sequence: Sequence, cycles: int):
    sequence.compile()
    awg_1.stop_all()
    awg_1.flush_waveform()
    awg_2.stop_all()
    awg_2.flush_waveform()
    if readout_port in sequence.port_list:
        awg_1.load_waveform(readout_port.waveform.real, 0, append_zeros=True)
        # plt.plot(readout_port.waveform.real);plt.show()
        awg_readout.queue_waveform(0, trigger="software/hvi", cycles=cycles)
    digi_ch.cycles(cycles)
    if len(digi_port.measurement_windows) == 0:
        acquire_start = 0
    else:
        acquire_start = int(digi_port.measurement_windows[0][0])
        acquire_end = int(digi_port.measurement_windows[-1][1])
        assert acquire_start % digi_ch.sampling_interval() == 0, f'{acquire_start}, {digi_ch.sampling_interval()}'
        assert acquire_end % digi_ch.sampling_interval() == 0
        points_per_cycle = (acquire_end - acquire_start) // digi_ch.sampling_interval()
        digi_ch.points_per_cycle(points_per_cycle)
    digi_ch.delay(acquire_start // digi_ch.sampling_interval())
    # print(f"points per cycle: {digi_ch.points_per_cycle()}")
    if ge_drive_port in sequence.port_list:
        # i, q = iq_corrector.correct(ge_port.waveform.conj())
        ge_drive = ge_drive_port.waveform.real
        # plt.plot(i);plt.show()
        awg_1.load_waveform(ge_drive, 1, append_zeros=True)
        #awg.load_waveform(q, 2, append_zeros=True)
        awg_qubit.queue_waveform(1, trigger="software/hvi", cycles=cycles)
        # awg_q2.queue_waveform(2, trigger="software/hvi", cycles=cycles)
    if gf_drive_port in sequence.port_list:
    # # i, q = iq_corrector.correct(ge_port.waveform.conj())
    #     twophoton = gf_drive_port.waveform.real
    #     # plt.plot(i);plt.show()
    #     awg_1.load_waveform(twophoton, 2, append_zeros=True)
    #     #awg.load_waveform(q, 2, append_zeros=True)
    #     awg_2pho.queue_waveform(2, trigger="software/hvi", cycles=cycles)

        i_2photon , q_2photon = iq_corrector_2photon.correct(gf_drive_port.waveform)
        # plt.plot(i_2photon);plt.show()
        # plt.plot(q_2photon);plt.show()
        awg_2.load_waveform(i_2photon, 2, append_zeros=True)
        awg_2.load_waveform(q_2photon, 3, append_zeros=True)
        awg_2photon_I.queue_waveform(2, trigger="software/hvi", cycles=cycles)
        awg_2photon_Q.queue_waveform(3, trigger="software/hvi", cycles=cycles)
        awg_2photon_I.dc_offset(iq_corrector_2photon.i_offset)
        awg_2photon_Q.dc_offset(iq_corrector_2photon.q_offset)
    if JPA_port in sequence.port_list :
        i, q = iq_corrector_JPA.correct(JPA_port.waveform)
        # JPA_pulse = JPA_port.waveform.real
        # plt.plot(i);plt.show()
        # plt.plot(q);plt.show()
        awg_2.load_waveform(i, 4, append_zeros=True)
        awg_2.load_waveform(q, 5, append_zeros=True)
        awg_JPA_I.queue_waveform(4, trigger="software/hvi", cycles=cycles)
        awg_JPA_Q.queue_waveform(5, trigger="software/hvi", cycles=cycles)
        awg_JPA_I.dc_offset(iq_corrector_JPA.i_offset)
        awg_JPA_Q.dc_offset(iq_corrector_JPA.q_offset)

    # awg_q2.queue_waveform(2, trigger="software/hvi", cycles=cycles)
    # if gh_port in sequence.port_list:
    #     # i, q = iq_corrector.correct(ge_port.waveform.conj())
    #     i = gh_port.waveform.real
    #     awg.load_waveform(i, 2, append_zeros=True)
    #     #awg.load_waveform(q, 2, append_zeros=True)
    #     awg_q2.queue_waveform(2, trigger="software/hvi", cycles=cycles)
    #     # awg_q2.queue_waveform(2, trigger="software/hvi", cycles=cycles)


def run2(sequence: Sequence, plot:bool=False, JPA_TD = False):
    try:
        lo_readout.output(True)
        awg_readout.start()
        digi_ch.start()
        if ge_drive_port in sequence.port_list:
            # lo_drive.output(True)
            awg_qubit.start()
        if gf_drive_port in sequence.port_list:
            lo_2pho.output(True)
            awg_2photon_I.start()
            awg_2photon_Q.start()
            # awg_2pho.start()
        if (JPA_port in sequence.port_list) & JPA_TD:
            # JPA_current_source.ramp_current(current_JPA,5e-7,0.1)
            # lo_JPA.output(True)
            awg_JPA_I.start()
            awg_JPA_Q.start()
            # awg_q2.start()
        hvi_trigger.output(True)
        data = digi_ch.read()
        # awg_1.stop_all()
        # awg_2.stop_all()
        digi_ch.stop()
        hvi_trigger.output(False)
        if plot:
            plt.plot(data.mean(axis=0))
            plt.show()
        return data
    finally:
        hvi_trigger.output(False)
        awg_1.stop_all()
        awg_2.stop_all()
        digi_ch.stop()
        lo_readout.output(False)
        # lo_drive.output(False)
        lo_2pho.output(False)
        # if JPA_TD:
            # # lo_JPA.output(False)
            # JPA_current_source.ramp_current(0, step=5e-7, delay=0)
            # JPA_current_source.off()



def split_data(data, measurement_windows):
    acquire_start = int(measurement_windows[0][0])
    datas = []
    for window in measurement_windows:
        start = (int(window[0]) - acquire_start) // digi_port.sampling_interval()
        end = (int(window[1]) - acquire_start) // digi_port.sampling_interval()
        datas.append(data[..., start:end])
    return datas

#To plot IQ plots
def IQ_plot(demod_data, tags, title, writer ):
    
    try:
        # plot_path = os.path.join(data_path + '\Images', measurement_name)
        for elem, tag in zip(demod_data, tags):
            plt.scatter(elem.real, elem.imag, s = 0.1,label=tag)
            # plt.hist2d(elem.real, elem.imag, bins=2000, cmin=1, norm=mcolors.LogNorm())
        plt.xlim([-100,100])
        plt.ylim([-100,100])
        plt.xlabel("In-phase (I)")
        plt.ylabel("Quadrature (Q)")
        plt.legend()
        plt.title(title)

       

        fig_dir = os.path.dirname(writer.filepath) + '/Images'
        os.makedirs(fig_dir, exist_ok=True)

        fig_filename = fig_dir + '/IQPlot.png'

        plt.savefig(fig_filename)
        plt.show()
    finally:
        writer.backup_file([fig_filename])

        #To plot IQ plots (histogram)
def IQ_plotHistogram(demod_data, tags, title, writer ):
    
    try:
        # plot_path = os.path.join(data_path + '\Images', measurement_name)
        for elem, tag in zip(demod_data, tags):
            # plt.scatter(elem.real, elem.imag, s = 0.1,label=tag)
            plt.hist2d(elem.real, elem.imag, bins=20, cmin=1, norm=mcolors.LogNorm())
        plt.xlim([-50,50])
        plt.ylim([-50,50])
        plt.xlabel("In-phase (I)")
        plt.ylabel("Quadrature (Q)")
        plt.legend()
        plt.title(title)

       

        fig_dir = os.path.dirname(writer.filepath) + '/Images'
        os.makedirs(fig_dir, exist_ok=True)

        fig_filename = fig_dir + '/IQPlotHist.png'

        plt.savefig(fig_filename)
        plt.show()
    finally:
        writer.backup_file([fig_filename])
    






