from setup_td import *
port=gf_drive_port
seq = Sequence(port_list = [port]) 
seq.add(Square(amplitude=0.5, duration=10000), port)

def pulse_continue(seq:Sequence=seq):
    seq.compile()
    ports = seq.port_list
    # if readout_port in ports:
    #     print("readout line")
    #     seq.compile()
    #     readout_pulse = readout_port.waveform.real
    #     awg1.load_waveform(readout_pulse, 0, append_zeros=True)
    #     awg_readout_I.queue_waveform(0, trigger="software/hvi", cycles=0, per_cycle=False)
    #     awg1.start_all()
    #     lo1.output(True)
    # elif qubit_drive_port in ports:
    #     waveform_i , waveform_q = iq_corrector_q.correct(qubit_drive_port.waveform)
    #     awg2.load_waveform(waveform_i, 0, append_zeros=True)
    #     awg2.load_waveform(waveform_q, 1, append_zeros=True)
    #     awg_Qdrive_I.queue_waveform(0, trigger="software/hvi", cycles=0, per_cycle=False)
    #     awg_Qdrive_Q.queue_waveform(1, trigger="software/hvi", cycles=0, per_cycle=False)
    #     awg2.start_all()
    #     lo2.output(True)
    # elif fogi_port in ports:
    #     waveform_i , waveform_q = iq_corrector_fogi.correct(fogi_port.waveform)
    #     awg2.load_waveform(waveform_i, 0, append_zeros=True)
    #     awg2.load_waveform(waveform_q, 1, append_zeros=True)
    #     awg_fogi_I.queue_waveform(0, trigger="software/hvi", cycles=0, per_cycle=False)
    #     awg_fogi_Q.queue_waveform(1, trigger="software/hvi", cycles=0, per_cycle=False)
    #     awg2.start_all()
    #     lo3.output(True)

    # elif gf_drive_port in ports:
    waveform_i , waveform_q = iq_corrector_2photon.correct(gf_drive_port.waveform)
    awg_2.load_waveform(waveform_i, 0, append_zeros=True)
    awg_2.load_waveform(waveform_q, 1, append_zeros=True)
    awg_2photon_I.queue_waveform(0, trigger="software/hvi", cycles=0, per_cycle=False)
    awg_2photon_Q.queue_waveform(1, trigger="software/hvi", cycles=0, per_cycle=False)
    awg_2.start_all()
    lo_2pho.output(True)
    # elif JPA_port in ports:
    #     i, q = iq_corrector_JPA.correct(JPA_port.waveform)
    #     awg1.load_waveform(i, 0, append_zeros=True)
    #     awg1.load_waveform(q, 1, append_zeros=True)
    #     awg_JPA_I.queue_waveform(0, trigger="auto", cycles=0, per_cycle=False)
    #     awg_JPA_Q.queue_waveform(1, trigger="auto", cycles=0, per_cycle=False)
    #     awg1.start_all()
    #     lo1.output(True)
    hvi_trigger.output(True)
    hvi_trigger.output(False)
    try:
        while True:
            'continue to send pulses'
    except KeyboardInterrupt:
        # awg1.stop_all()
        awg_2.stop_all()
        # awg.stop_all()
        # lo1.output(False)
        # lo2.output(False)
        # lo3.output(False)
        lo_2pho.output(False)
        print('AWG and LO are turned off')

pulse_continue()