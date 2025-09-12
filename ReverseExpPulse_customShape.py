
from sequence_parser.instruction.pulse import Pulse, PulseShape
import copy
import numpy as np


import os

import matplotlib.pyplot as plt
import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer
from sequence_parser import Port, Sequence, Variable, Variables
from tqdm import tqdm
import qcodes as qc
import qcodes.utils.validators as vals
from plottr.data.datadict_storage import search_datadict

#pulse form

basedir = r"D:/Redza/Logs"
show_plots =True
#Fido function to obtain monitr files
def Fido(datetime, name):          #Fido gets your raw _data for you!
    foldername, datadict = search_datadict(basedir, datetime, name=name , newest = True, only_complete=False)
    # print(foldername)
    # print(datadict)
    return foldername, datadict


# foldernamePhoton, datadict_Photon = Fido("2025-06-05T224958","td_2photon_electricfieldcheck_NoJPA")
foldernamePhoton, datadict_Photon  = Fido("2025-06-07T175140", "td_2photon_electricfieldcheck_NoJPA")
signal = datadict_Photon['waveform']['values'][0]
time= datadict_Photon["time"]["values"][0]*1e-9



if show_plots == True:
    #check original waveform
    fig, ax = plt.subplots()
    ax.plot(time, signal)
    plt.show()





# reversing photon shape
rev_sig = [signal[-i] for i in np.arange(len(signal))]
# print(signal[10])
# print(rev_sig[-10])




if show_plots == True:
    #check reverse waveform
    fig, ax = plt.subplots()
    ax.plot(time,rev_sig)
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

fft_time, fft_signal = fourier_tr(time, rev_sig)
# fft_time = fft_time + readout_lo_freq*1e9           #Shifting according to the demodulation frequency




if show_plots == True:
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
    plt.show()

#filtering 


def bandpass_filter(freqs, signal, f_low, f_high):

    freqs = np.array(freqs)
    signal = np.array(signal)

    # Create a boolean mask for frequencies within the band
    band_mask = (freqs >= f_low) & (freqs <= f_high)

    # Zero out components outside the band
    filtered_signal = np.where(band_mask, signal, 0)

    return filtered_signal



fft_signal = bandpass_filter(fft_time, fft_signal, -0.152e9,  -0.144e9)




if show_plots == True:
    
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
    plt.show()


#Inverse Fourier

# Perform inverse Fourier transform
reconstructed_signal =2* np.fft.ifft(fft_signal)
# reconstructed_time = np.fft.ifft(fft_time)


if show_plots == True:
    
    plt.figure(figsize=(10, 4))
    plt.plot(time, rev_sig, label='Original reversed Signal')
    plt.plot(time, reconstructed_signal, '--', label='Reconstructed reversed Signal (IFFT)')
    # plt.plot(time, 2*reconstructed_signal_imag, '--', color = 'red',label='Imaginary Reconstructed Signal (IFFT)')
    # plt.plot(time, 2*np.abs(reconstructed_signal), '--', color = 'black',label='Norm of Reconstructed Signal (IFFT)')
    plt.legend()
    plt.title('Original vs Reconstructed Signal')
    plt.xlabel('Time')
    plt.ylabel('Amplitude')
    plt.tight_layout()

    print(np.angle(reconstructed_signal))
    plt.show()



####Cleanup of final pulse

# time and signal are 1D arrays of the same length

# t_start = 4.e-7  # set your desired time range
# t_end = 2.25e-6


t_start = 1e-5  # set your desired time range
t_end = 2.5e-5

# Create a mask: True where time is in [t_start, t_end]
mask = (time >= t_start) & (time <= t_end)

# Apply mask to signal: keep values where mask is True, zero elsewhere
# filtered_signal = np.where(mask, signal, 0)

og_signal = reconstructed_signal
signal = np.where(mask,reconstructed_signal, 0)

if show_plots == True:
    
    plt.figure(figsize=(10, 4))
    plt.plot(time, og_signal, label='Original Signal', alpha=0.5)
    plt.plot(time, signal, label='Windowed Signal', linewidth=2)
    plt.title('Signal Windowed in Time Domain')
    plt.xlabel('Time')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.tight_layout()

    plt.show()


#extracting array values
waveform_array = []

for value in signal:
    if value != 0:
        waveform_array.append(value)

if show_plots == True:
        

    plt.figure(figsize=(10, 4))
    plt.plot(np.arange(len(waveform_array)), waveform_array, alpha=0.5)
    plt.title('AWG_ signal')
    plt.xlabel('AWG_ time unit')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.tight_layout()
    plt.show()



# #interpolating the waveform
# waveform_interpolated = []

# for i in range(len(waveform_array)-1):
#     waveform_interpolated.append(waveform_array[i])
#     waveform_interpolated.append(np.mean([waveform_array[i],waveform_array[i+1]]))


# plt.figure(figsize=(10, 4))
# plt.plot(np.arange(len(waveform_interpolated)), waveform_interpolated, alpha=0.5)
# plt.title('AWG_ signal')
# plt.xlabel('AWG_ time unit')
# plt.ylabel('Amplitude')
# plt.legend()
# plt.tight_layout()


# if show_plots == True:
#     plt.show()

# print(waveform_array[0])

# print(type(waveform_array))

#converting to ndarray

waveform_ndarray = np.array(waveform_array)
# print(type(waveform_ndarray))
# print(waveform_ndarray.shape)


#converting to pulse class
class ReversePhotonShape(PulseShape):
    def __init__(self):
        super().__init__()
        
    def set_params(self, pulse):
        self.amplitude = pulse.tmp_params["amplitude"]
        self.duration = pulse.duration

    def model_func(self, time):
        #time uses relative time, so find a way to re-translate that into time list index
        # print(time)
        # print(time - time[0])
        waveform = np.abs(waveform_ndarray) 
        # print(waveform)
        # print(waveform_array.shape)
        return waveform

class ReversePhoton(Pulse):
    def __init__(
        self,
        # amplitude = 1,
        # duration = 100,
        zero_end = False,
    ):
        super().__init__()
        self.pulse_shape = ReversePhotonShape()
        self.params = {
            "amplitude" : max(waveform_ndarray),
            "duration" : len(waveform_ndarray),
            "zero_end" : zero_end
        }

    def _get_duration(self):
        self.duration = self.tmp_params["duration"]

readout_port = Port("readout_port", if_freq =1, max_amp=1.5)

# show_plots = False
seq = Sequence([readout_port])
seq.add(ReversePhoton(zero_end=False), readout_port)

seq.draw()