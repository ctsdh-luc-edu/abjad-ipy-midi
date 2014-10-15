# -*- coding: utf-8 -*-
'''
Abjad-IPython: MIDI Playback
----------------------------

Integrates audio rendering of Abjad MIDI files into IPython notebooks using
`fluidsynth`.

This patch requires `fluidsynth` be in your $PATH. If you do not have
`fluidsynth` installed, it is likely available in your platform's package
manager:

OS X
    $ brew install fluidsynth --with-libsndfile
    $ port install fluidsynth

Linux
    $ apt-get install fluidsynth

'''

import os
import os.path
import shutil
import tempfile
from IPython.core.display import display_html


#
# Global (module) variables set by load_sound_font() only
#

sound_font = None
midi_bank = 'gs'


def display_mp3(mp3_file_path, ogg_file_path):
    from abjad.tools import systemtools
    ffmpeg_command = 'ffmpeg -i {} {}'.format(ogg_file_path, mp3_file_path)
    print(ffmpeg_command)
    result = systemtools.IOManager.spawn_subprocess(ffmpeg_command)
    if result == 0:
        encoded_audio = get_b64_from_file(mp3_file_path)
        audio_tag = '<audio controls type="audio/mpeg" '
        audio_tag += 'src="data:audio/mpeg;base64,{}">'
        audio_tag = audio_tag.format(encoded_audio)
        display_html(audio_tag, raw=True)
        return True
    message = 'ffmpeg failed to render OGG as MP3, result: {!i}'
    message = message.format(result)
    print(message)
    return False


def display_ogg(midi_file_path, ogg_file_path):
    from abjad.tools import systemtools
    fluidsynth_command = (
        'fluidsynth'
        '-T oga'
        '-nli'
        '-r 44200'
        '-o synth.midi-bank-select={}'.format(midi_bank),
        '-F',
        ogg_file_path,
        sound_font,
        midi_file_path,
        )
    fluidsynth_command = ' '.join(fluidsynth_command)
    print(fluidsynth_command)
    result = systemtools.IOManager.spawn_subprocess(fluidsynth_command)
    if result == 0:
        encoded_audio = get_b64_from_file(ogg_file_path)
        audio_tag = '<audio controls type="audio/ogg" '
        audio_tag += 'src="data:audio/ogg;base64,{}">'
        audio_tag = audio_tag.format(encoded_audio)
        display_html(audio_tag, raw=True)
        return True
    message = 'fluidsynth failed to render MIDI as OGG, result: {!i}'
    message = message.format(result)
    print(message)
    return False


def get_b64_from_file(file_name):
    '''Read the base64 representation of a file and encode for HTML.
    '''
    import base64
    import sys
    with open(file_name, 'rb') as file_pointer:
        data = file_pointer.read()
        if sys.version_info[0] == 2:
            return base64.b64encode(data).decode('utf-8')
        return base64.b64encode(data)


def load_ipython_extension(ipython):
    import abjad
    from abjad.tools import topleveltools
    abjad.play = play
    topleveltools.play = play
    ipython.push({'play': play})
    ipython.push({'load_sound_font': load_sound_font})


def load_sound_font(new_sound_font, new_midi_bank):
    '''Save location of argument sound_font and its type.

    Type can be either 'gs', 'gm', 'xg', or 'mma'.
    '''
    global sound_font
    global midi_bank
    if os.path.isfile(new_sound_font):
        sound_font = new_sound_font
    else:
        message = 'The specified sound_font {} (relative to {}) '
        message += 'is either inaccessible or does not exist.'
        message = message.format(new_sound_font, os.getcwd())
        print(message)
    valid_midi_banks = ('gs', 'gm', 'xg', 'mma')
    if new_midi_bank in valid_midi_banks:
        midi_bank = new_midi_bank
    else:
        message = 'The MIDI bank must be either be one of {!s}'
        message = message.format(valid_midi_banks)
        print(message)


def play(expr):
    '''Render `expr` as Vorbis audio and display it in the IPython notebook
    as an <audio> tag.

    This function requires `fluidsynth` and `ffmpeg` to convert MIDI into an
    audio recording.
    '''
    from abjad.tools import systemtools
    from abjad.tools import topleveltools
    global sound_font
    global midi_bank
    if not systemtools.IOManager.find_executable('fluidsynth'):
        print('fluidsynth is not available.')
    if not systemtools.IOManager.find_executable('ffmpeg'):
        print('ffmpeg is not available.')
    assert '__illustrate__' in dir(expr)
    if not sound_font:
        message = 'sound_font is not specified, please call '
        message += "'load_sound_font(sound_font, midi_bank)\'"
        print(message)
        return
    temp_directory = tempfile.mkdtemp()
    midi_file_path = os.path.join(temp_directory, 'out.mid')
    result = topleveltools.persist(expr).as_midi(midi_file_path)
    midi_file_path, format_time, render_time = result
    ogg_file_path = os.path.join(temp_directory, 'out.ogg')
    mp3_file_path = os.path.join(temp_directory, 'out.mp3')
    rendered_successfully = display_ogg(midi_file_path, ogg_file_path)
    if rendered_successfully:
        display_mp3(mp3_file_path, ogg_file_path)
    shutil.rmtree(temp_directory)