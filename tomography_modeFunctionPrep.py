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
# show_plots =True
show_plots =False
#Fido function to obtain monitr files
def Fido(datetime, name):          #Fido gets your raw _data for you!
    foldername, datadict = search_datadict(basedir, datetime, name=name , newest = True, only_complete=False)
    print(foldername)
    print(datadict)
    return foldername, datadict



foldernamePhoton, datadict_Photon  = Fido("2025-09-24T193301", "tomography_modeFunctionGet")

#Defining variables
signal = datadict_Photon['waveform']['values']
time= datadict_Photon["time"]["values"]*1e-9

#check original waveform
fig, ax = plt.subplots()
ax.plot(time, signal)

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
axs[0].plot(fft_time, np.abs(fft_signal))
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


def bandpass_filter(freqs, signal, f_low, f_high):

    freqs = np.array(freqs)
    signal = np.array(signal)

    # Create a boolean mask for frequencies within the band
    band_mask = (freqs >= f_low) & (freqs <= f_high)

    # Zero out components outside the band
    filtered_signal = np.where(band_mask, signal, 0)

    return filtered_signal


fft_signal = bandpass_filter(fft_time, fft_signal, readout_freq*1e9 - 0.005e9, readout_freq*1e9 + 0.005e9)

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
# reconstructed_time = np.fft.ifft(fft_time)

#For final output
output = reconstructed_signal

reconstructed_signal = reconstructed_signal * np.exp(-1j * 2*np.pi * (readout_lo_freq) * time )


#phase correction
phase = np.unwrap(np.angle(reconstructed_signal))
reconstructed_signal *= np.exp(-1j * (phase ))

# Reconstructed signal is complex; take the real part if expected
reconstructed_signal_real = np.real(reconstructed_signal)
reconstructed_signal_imag = np.imag(reconstructed_signal)

plt.figure(figsize=(10, 4)) 
plt.plot(time, signal, label='Original Signal')
plt.plot(time, 2*reconstructed_signal_real, '--', label='Real Reconstructed Signal (IFFT)')
plt.plot(time, 2*reconstructed_signal_imag, '--', color = 'red',label='Imaginary Reconstructed Signal (IFFT)')
# plt.plot(time, 2*np.abs(reconstructed_signal), '--', color = 'black',label='Norm of Reconstructed Signal (IFFT)')
plt.legend()
plt.title('Original vs Reconstructed Signal')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.tight_layout()


if show_plots == True:
    plt.show()

#Export envelope as mode function
# print(type(reconstructed_signal_real[0]))
# mode_function = [i for i in reconstructed_signal_real]
mode_function = reconstructed_signal_real
# print(type(mode_function))
