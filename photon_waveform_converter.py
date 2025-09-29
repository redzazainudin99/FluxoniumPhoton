from plottr.data.datadict_storage import datadict_from_hdf5
from plottr.data.datadict_storage import DataDict, DDH5Writer
from plottr.data.datadict_storage import search_datadict
import numpy as np
import matplotlib.pyplot as plt
import os
from pprint import pprint
from tqdm import tqdm
from datetime import datetime
import pandas as pd
import copy
import itertools
# import scqubits as scq
import csv
from sklearn.decomposition import PCA
from scipy.signal import find_peaks
from lmfit import Model
from setup_td import *

basedir = r"D:/Redza/Logs"
show_plots =True
#Fido function to obtain monitr files
def Fido(datetime, name):          #Fido gets your raw _data for you!
    foldername, datadict = search_datadict(basedir, datetime, name=name , newest = True, only_complete=False)
    print(foldername)
    print(datadict)
    return foldername, datadict


foldernamePhoton, datadict_Photon = Fido("2025-06-02T230203","td_2photon_electricfieldcheck_JPACheck_delayedDrive")


# foldernamePhoton, datadict_Photon = Fido("2025-06-02T190923","td_2photon_electricfieldcheck_JPACheck_delayedDrive")



#Defining variables
signal = datadict_Photon['waveform']['values'][0]
time= datadict_Photon["time"]["values"][0]*1e-9

#check original waveform
fig, ax = plt.subplots()
ax.plot(time, signal)

if show_plots == True:
    plt.show()



############limiting the waveform to only a section of the time################

# time and signal are 1D arrays of the same length

t_start = 0#5.8e-7  # set your desired time range
t_end = 10#2.2e-6

# Create a mask: True where time is in [t_start, t_end]
mask = (time >= t_start) & (time <= t_end)

# Apply mask to signal: keep values where mask is True, zero elsewhere
# filtered_signal = np.where(mask, signal, 0)

og_signal = signal
signal = np.where(mask, signal, 0)

plt.figure(figsize=(10, 4))
plt.plot(time, og_signal, label='Original Signal', alpha=0.5)
plt.plot(time, signal, label='Windowed Signal', linewidth=2)
plt.title('Signal Windowed in Time Domain')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.legend()
plt.tight_layout()


if show_plots == True:
    plt.show()


################Fourier analysis and cleanup

def fourier_tr(x,y, sort=False):
    off_ini = np.mean(y)
    y_mod = y - off_ini
    N = len(y)
    x_fft = np.fft.fftfreq(N,d=x[1]-x[0])
    y_fft = np.fft.fft(y_mod)
    if sort:
        sorted_idx = np.argsort(x_fft)
        x_fft = x_fft[sorted_idx]
        y_fft = y_fft[sorted_idx]
    return x_fft,y_fft

fft_time, fft_signal = fourier_tr(time, signal)
fft_time = fft_time + readout_lo_freq*1e9           #Shifting according to the demodulation frequency
fig, axs = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

# Plot real part
axs[0].plot(fft_time, np.real(fft_signal))
axs[0].set_title('Real Part of FFT Signal')
axs[0].set_ylabel('Amplitude')

# Plot imaginary part
axs[1].plot(fft_time, np.imag(fft_signal))
axs[1].set_title('Imaginary Part of FFT Signal')
axs[1].set_xlabel('Frequency')
axs[1].set_ylabel('Amplitude')

plt.tight_layout()

if show_plots == True:
    plt.show()


##Filter cleanup

#filter function
def peak_filter(signal, threshold_coefficient):
    threshold = threshold_coefficient * np.max(np.abs(signal))  # or set manually
    filtered_fft_signal = np.where(np.abs(signal) > threshold, signal, 0)

    return filtered_fft_signal

fft_signal = peak_filter(fft_signal, 0.1)


fig, axs = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

# Plot real part
axs[0].plot(fft_time, np.real(fft_signal))
axs[0].set_title('Real Part of FFT Signal')
axs[0].set_ylabel('Amplitude')

# Plot imaginary part
axs[1].plot(fft_time, np.imag(fft_signal))
axs[1].set_title('Imaginary Part of FFT Signal')
axs[1].set_xlabel('Frequency')
axs[1].set_ylabel('Amplitude')

plt.tight_layout()



if show_plots == True:
    plt.show()


#Inverse Fourier

# Perform inverse Fourier transform
reconstructed_signal = np.fft.ifft(fft_signal)

# Reconstructed signal is complex; take the real part if expected
reconstructed_signal = np.real(reconstructed_signal)

plt.figure(figsize=(10, 4))
plt.plot(time, signal, label='Original Signal')
plt.plot(time, reconstructed_signal, '--', label='Reconstructed Signal (IFFT)')
plt.legend()
plt.title('Original vs Reconstructed Signal')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.tight_layout()


if show_plots == True:
    plt.show()


####Cleanup of final pulse

# time and signal are 1D arrays of the same length

# t_start = 4.e-7  # set your desired time range
# t_end = 2.25e-6


t_start = 5.5e-7  # set your desired time range
t_end = 2.e-6

# Create a mask: True where time is in [t_start, t_end]
mask = (time >= t_start) & (time <= t_end)

# Apply mask to signal: keep values where mask is True, zero elsewhere
# filtered_signal = np.where(mask, signal, 0)

og_signal = reconstructed_signal
signal = np.where(mask, reconstructed_signal, 0)


plt.figure(figsize=(10, 4))
plt.plot(time, og_signal, label='Original Signal', alpha=0.5)
plt.plot(time, signal, label='Windowed Signal', linewidth=2)
plt.title('Signal Windowed in Time Domain')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.legend()
plt.tight_layout()


if show_plots == True:
    plt.show()

#extracting array values
waveform_array = []

for value in signal:
    if value != 0:
        waveform_array.append(value)


#interpolating the waveform
waveform_interpolated = []

for i in len(waveform_array):
    waveform_interpolated.append(waveform_array[i])
    waveform_interpolated.append(np.mean(waveform_array[i],waveform_array[i+1]))


plt.figure(figsize=(10, 4))
plt.plot(np.arange(len(waveform_array)), waveform_array, alpha=0.5)
plt.title('AWG_ signal')
plt.xlabel('AWG_ time unit')
plt.ylabel('Amplitude')
plt.legend()
plt.tight_layout()


if show_plots == True:
    plt.show()




#interpolating the waveform
waveform_interpolated = []

for i in range(len(waveform_array)):
    waveform_interpolated.append(waveform_array[i])
    
    if i<len(waveform_array) - 1:
        waveform_interpolated.append(np.mean(waveform_array[i],waveform_array[i+1]))



plt.figure(figsize=(10, 4))
plt.plot(np.arange(len(waveform_interpolated)), waveform_interpolated, alpha=0.5)
plt.title('AWG_ signal')
plt.xlabel('AWG_ time unit')
plt.ylabel('Amplitude')
plt.legend()
plt.tight_layout()


if show_plots == True:
    plt.show()


#flipping array
reversed_photon = np.array(list(reversed(waveform_interpolated)))
print(len(reversed_photon))

if len(reversed_photon)%2 !=0:
    reversed_photon  = np.delete(reversed_photon , -1)


plt.figure(figsize=(10, 4))
plt.plot(np.arange(len(reversed_photon)),reversed_photon, alpha=0.5)
plt.title('AWG_ signal')
plt.xlabel('AWG_ time unit')
plt.ylabel('Amplitude')
plt.legend()
plt.tight_layout()


if show_plots == True:
    plt.show()

#adding this waveform as a pulse class

def append_waveform(seq:Sequence, append_port:Port, waveform_appended:np.ndarray):
    seq.compile()
    waveform_dict = dict()
    for port in seq.port_list:
        waveform = port.waveform
        windows = port.measurement_windows
        if port.name == append_port.name:
            for window in windows:
                try:
                    if window[1] - window[0] == len(waveform_appended):
                        waveform[int(window[0]) : int(window[1])] = waveform_appended
                        if 0:print(f"appended : {append_port.name}, {window[0]}~{window[1]}")
                    else:waveform[int(window[0]) : int(window[1])] = np.zeros(int(window[1] - window[0]));print(f"zeros appended : {append_port.name}, {window[0]}~{window[1]}")
                except:
                    if 1:print(f"not appended : {append_port.name}, {window[0]}~{window[1]}")
                    pass
        waveform_dict[port.name] = waveform
    return waveform_dict


def load_sequence_append(waveform_appended, append_port,sequence: Sequence, cycles: int):
    waveform_dict = append_waveform(sequence, append_port, waveform_appended)
    awg_1.stop_all();    awg_1.flush_waveform()
    awg_2.stop_all();    awg_2.flush_waveform()

    if readout_port in sequence.port_list:
        awg_1.load_waveform(waveform_dict[readout_port.name].real, 0, append_zeros=True)
        # awg_1.load_waveform(readout_port.waveform.real, 0, append_zeros=True)
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
        ge_drive = waveform_dict[ge_drive_port.name]
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

        i_2photon , q_2photon = iq_corrector_2photon.correct(waveform_dict[gf_drive_port.name])
        # plt.plot(i_2photon);plt.show()
        # plt.plot(q_2photon);plt.show()
        awg_2.load_waveform(i_2photon, 2, append_zeros=True)
        awg_2.load_waveform(q_2photon, 3, append_zeros=True)
        awg_2photon_I.queue_waveform(2, trigger="software/hvi", cycles=cycles)
        awg_2photon_Q.queue_waveform(3, trigger="software/hvi", cycles=cycles)
        awg_2photon_I.dc_offset(iq_corrector_2photon.i_offset)
        awg_2photon_Q.dc_offset(iq_corrector_2photon.q_offset)
    if JPA_port in sequence.port_list :
        i, q = iq_corrector_JPA.correct(waveform_dict[JPA_port.name])
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


