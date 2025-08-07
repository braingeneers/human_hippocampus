#!/usr/bin/env python3  


import numpy as np
from matplotlib import pyplot as plt
from scipy import signal
import pickle
from h5py import File
import pandas as pd
import braingeneers.data.datasets_electrophysiology as ephys

def pickle_mxw(file_path, save_path, well_no = 0, rec_no = 0, downsample_rate=20, start_s = 0, length_s = 10):
    """
    Converts a raw MaxWell h5 file into the .pkl format necessary for data processing by this toolbox.

    Input:
        file_path: the filepath and filename for the .raw.h5 file
        save_path: the filepath and filename with which to save the .pkl file
        well_no: the well number of the data to save
        rec_no: the recording number of the data to save
        downsample_rate: The rate at which to downsample. The effective sampling frequency after downsampling becomes the original frequency (20k Hz for the MaxOne) divided by downsample_rate.
        start_s: the start time of the recording in seconds
        length_s: the length of the resulting recording data in seconds
    """
    h5_file = File(file_path)

    print("Loading data...")
    try:
        parent_folder = h5_file[f"wells/well{well_no:03}/rec{rec_no:04}"]
        sampling_rate = int(parent_folder["settings/sampling"][0])
        raw_data = np.array(parent_folder["groups/routed/raw"][:, start_s * sampling_rate: (start_s + length_s) * sampling_rate])
        channel_map = pd.DataFrame(np.array(parent_folder["settings/mapping"])).values
    except KeyError:
        print("H5 paths not found, trying with old file format...")
        sampling_rate = 20000
        raw_data = (np.array(h5_file["sig"][:, start_s * sampling_rate: (start_s + length_s) * sampling_rate]))#convert to mV
        channel_map = pd.DataFrame(np.array(h5_file["mapping"])).values

    data_down = []  # the variable that will hold the downsambled data
    for i, channel_num in enumerate(channel_map[:,0].astype(int)) : # we gather data for ever channel that was recorded from, (these channels are in the channel map of the metadata)
        data_down.append( signal.decimate( raw_data[i,:], downsample_rate )  ) # we get everyt 20th data point, and then append it to the data_down variable
    del raw_data
    data_down = np.array( data_down ) # we turn the data into an np.array for easier future analysis

    print("Saving Data...")
    to_pickle = {"data": data_down, "xy": channel_map[:,2:4], "frame_rate": sampling_rate/downsample_rate, "start_time": start_s, "stop_time": start_s + length_s, "file": file_path}

    del data_down
    with open( save_path, 'wb') as filename:
        pickle.dump( to_pickle, filename)
    print("Done!")


def data_get_experiments(uuid):
    """
    Input uuid: the uuid of the experiment
    Output: Prints the filename corresponding to each experiment
    """
    metadata = ephys.load_metadata(uuid)
    for key,val in metadata["ephys_experiments"].items():
        print( key," - ", val["blocks"][0]["path"] )


def data_create(uuid, experiment_name, start_s, save_path, length_s=10):
    """
    Input:
        uuid: the uuid of the experiment
        experiment_name: the name of the experiment corresponding to the file on interest
        start_s: the start time of the recording in seconds
        save_path: the path to save for the data (must be a pickle file)
        length_s: the length of the resulting recording data in seconds 
    Output: Saves the data to save_path
    """
    print("Loading Data... might take up to 10min")
    metadata = ephys.load_metadata(uuid)
    raw_data = ephys.load_data( metadata=metadata, experiment=experiment_name, offset=start_s*20000, length=length_s*20000, channels=None )
    channel_map = np.array( metadata['ephys_experiments'][experiment_name]["mapping"] )

    data_down = []  # the variable that will hold the downsambled data
    for i in channel_map[:,0].astype(int) : # we gather data for ever channel that was recorded from, (these channels are in the channel map of the metadata)
        data_down.append( signal.decimate( raw_data[i,:], 20 )  ) # we get everyt 20th data point, andthen append it to the data_down variable
    del raw_data
    data_down = np.array( data_down ) # we turn the data into an np.array for easier future analysis

    print("Saving Data...")
    to_pickle = {"data": data_down, "xy": channel_map[:,1:3], "frame_rate": 20000/20, "uuid":uuid,
                  "file": metadata["ephys_experiments"][experiment_name]["blocks"][0]["path"] }
    del data_down
    with open( save_path, 'wb') as filename:
        pickle.dump( to_pickle, filename)
    print("Done!")



