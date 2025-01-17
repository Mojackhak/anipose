#!/usr/bin/env python3

import os.path

# Dependencies for video:
import os
from glob import glob
import io
from contextlib import redirect_stdout

from .common import natural_keys, make_process_fun

def rename_dlc_files(folder, base):
    files = glob(os.path.join(folder, base+'*'))
    for fname in files:
        basename = os.path.basename(fname)
        # compatibility with DLC 3.0
        _, ext = os.path.splitext(basename)
        if ext != '.h5' and ext != '.csv':
            _, ext = basename.rsplit('_', 1)
            ext = '_' + ext
        os.rename(os.path.join(folder, basename),
                  os.path.join(folder, base + ext))


def process_session(config, session_path):
    pipeline_videos_raw = config['pipeline']['videos_raw']
    pipeline_pose = config['pipeline']['pose_2d']
    shuffle = config['shuffle']
    save_as_csv = config['save_as_csv']
    video_ext = config['video_extension']

    config_name = os.path.join(config['model_folder'], 'config.yaml')

    source_folder = os.path.join(session_path, pipeline_videos_raw)
    outdir = os.path.join(session_path, pipeline_pose)

    videos = glob(os.path.join(source_folder, '*.'+video_ext))
    videos = sorted(videos, key=natural_keys)

    if len(videos) > 0:
        os.makedirs(outdir, exist_ok=True)

    videos_to_process = []
    for video in videos:
        basename = os.path.basename(video)
        basename, ext = os.path.splitext(basename)

        dataname = os.path.join(outdir, basename + '.h5')
        if os.path.exists(dataname):
            continue
        else:
            rename_dlc_files(outdir, basename) # try renaming in case it processed before
            if os.path.exists(dataname):
                print(video)
                continue
            else:
                videos_to_process.append(video)
                
    print(f"Analyzing videos with DeepLabCut: {config_name} shuffle={shuffle} save_as_csv={save_as_csv}")

    if len(videos_to_process) > 0:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        import deeplabcut
        trap = io.StringIO()
        for i in range(0, len(videos_to_process), 5):
            batch = videos_to_process[i:i+5]
            for video in batch:
                print(video)
            with redirect_stdout(trap):
                deeplabcut.analyze_videos(config_name, batch,
                                          videotype=video_ext, shuffle=shuffle, save_as_csv=save_as_csv,
                                          destfolder=outdir, TFGPUinference=True,
                                          allow_growth=True, use_openvino=False)
            for video in batch:
                basename = os.path.basename(video)
                basename, ext = os.path.splitext(basename)
                rename_dlc_files(outdir, basename)


pose_videos_all = make_process_fun(process_session)
