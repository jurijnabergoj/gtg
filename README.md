# Guitar Tablature Generator

This application records audio from a guitar, detects the notes being played, and generates tablature in real-time with synchronized playback.

## Requirements

### Python Version
- Python 3.8 or higher

### Required Python Packages
```bash
pip install pyaudio
pip install numpy
pip install aubio
pip install scipy
pip install matplotlib
pip install PyMuPDF
pip install pygame
pip install Pillow
```

### Audio Input
- Working microphone or audio input device
- Guitar

## File Structure
The application consists of four main Python files:
- `AudioProcessor.py`: Handles audio input and note detection
- `TablatureVisualizer.py`: Creates the visual representation of the tablature
- `generate_tablature.py`: Main script for real-time tablature generation
- `display_tablature.py`: Playback script with synchronized visualization

## How to Run

1. First, generate the tablature:
```bash
python generate_tablature.py
```
This will:
- Start recording audio from your default input device
- Generate a tablature in real-time
- Save the following files:
  - `output_audio.wav`: The recorded audio
  - `output_tab.txt`: Timing data for the notes
  - `final_tablature.pdf`: The generated tablature in PDF format

2. Then, play back the recording with synchronized visualization:
```bash
python display_tablature.py
```

## Troubleshooting

### Audio Input Issues
- Make sure your microphone/audio input is set as the default input device
- Check system permissions for microphone access
- Verify that PyAudio can detect your input device

### Visualization Issues
- If the display window doesn't appear, check that matplotlib is properly installed
- For PDF rendering issues, verify that PyMuPDF (fitz) is correctly installed

### Note Detection Issues
- Ensure your guitar is properly tuned (standard tuning: E A D G B E)
- Position the microphone close to the guitar for better audio quality
- Adjust your input volume if notes aren't being detected

## Technical Details

### Guitar Tuning
The application is configured for standard guitar tuning:
- E2: 82.41 Hz
- A2: 110.00 Hz
- D3: 146.83 Hz
- G3: 196.00 Hz
- B3: 246.94 Hz
- E4: 329.63 Hz

### Performance
- Buffer Size: 1024 samples
- Sample Rate: 44100 Hz
- Pitch Detection Algorithm: Aubio default
- Maximum fret detection: up to fret 20
