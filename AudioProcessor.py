import pyaudio
import numpy as np
import aubio
import time
import threading
from scipy.io.wavfile import write

# Guitar constants
guitar_tuning = [82.41, 110.00, 146.83, 196.00, 246.94, 329.63]  # E2, A2, D3, G3, B3, E4
string_names = ["E", "A", "D", "G", "B", "e"]
MAX_MOVEMENT_COST = 8


class AudioProcessor:
    def __init__(self):
        self.buffer_size = 1024
        self.samplerate = 44100
        self.recording = False
        self.frames = []
        self.last_three_notes = []
        self.note_active = None
        self.note_last_time = 0
        self.note_signal_max = 0
        self.NOTE_REPEAT_THRESHOLD = 0.7
        self.NOTE_PAUSE_THRESHOLD = 3
        self.start_offset = None

        # PyAudio setup
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.samplerate,
            input=True,
            frames_per_buffer=self.buffer_size,
            stream_callback=self.audio_callback
        )

        # Aubio setup
        win_s = 4096
        self.pitch_o = aubio.pitch("default", win_s, self.buffer_size, self.samplerate)
        self.pitch_o.set_unit("Hz")
        self.pitch_o.set_tolerance(0.2)

        # Clear output file
        with open("output_tab.txt", "w") as f:
            pass

    def audio_callback(self, in_data, frame_count, time_info, status):
        if self.recording:
            self.frames.append(in_data)

        signal = np.frombuffer(in_data, dtype=np.float32)
        self.process_audio(signal)

        return in_data, pyaudio.paContinue

    def start_recording(self, duration):
        print("Starting recording and note detection...")
        self.recording = True
        self.frames = []
        self.start_offset = time.time()

        # Start recording
        def stop_recording():
            start_time = time.time()
            while time.time() - start_time < duration and self.recording:
                time.sleep(0.1)
            self.recording = False
            self.save_recording("output_audio.wav")

        threading.Thread(target=stop_recording).start()
        self.stream.start_stream()

    def save_recording(self, filename):
        print(f"Saving recording to {filename}")
        audio_data = np.frombuffer(b''.join(self.frames), dtype=np.float32)
        audio_data = (audio_data * 32767).astype(np.int16)
        write(filename, self.samplerate, audio_data)
        print(f"Recording saved to {filename}")

    def process_audio(self, signal):
        pitch = self.pitch_o(signal)[0]
        confidence = self.pitch_o.get_confidence()
        current_time = time.time()

        if confidence > -0.7:
            positions = self.find_tab_positions(pitch)
            if positions:
                selected_position = self.select_appropriate_string2(positions)
                if not selected_position:
                    return

                if ((not self.note_active) or
                        (self.note_active["position"] != selected_position) or
                        ((self.note_active["position"] == selected_position) and
                         (current_time - self.note_last_time > self.NOTE_REPEAT_THRESHOLD) and
                         (abs(self.note_signal_max - signal.max()) <= 0.01))):
                    self.note_active = {
                        "position": selected_position,
                        "start_time": current_time,
                    }
                    self.note_last_time = current_time
                    self.note_signal_max = signal.max()
                    self.save_note_to_file(self.note_active)
                    self.update_last_three_notes(selected_position)
                    print(
                        f"Pitch: {pitch:.2f} Hz, Tablature: {selected_position}, Time: {current_time - self.start_offset:.2f}")

    def find_tab_positions(self, frequency):
        """Map detected frequency to guitar tablature positions."""
        if frequency == 0:
            return None
        note_positions = []
        for i, base_freq in enumerate(guitar_tuning):
            for fret in range(0, 21):
                note_freq = base_freq * (2 ** (fret / 12))
                if abs(note_freq - frequency) < 3:
                    note_positions.append((string_names[i], fret))
                    break
        return note_positions

    def select_appropriate_string2(self, positions):
        if not positions:
            return None

        def movement_cost(position):
            string, fret = position
            cost = 0

            for i, recent_note in enumerate(reversed(self.last_three_notes)):
                prev_string, prev_fret = recent_note
                weight = 1 / (i + 1)
                string_change = abs(string_names.index(string) - string_names.index(prev_string))
                fret_change = abs(fret - prev_fret)
                cost += weight * np.sqrt(string_change ** 2 + fret_change ** 2)

            cost += 0.1 * fret
            return cost

        current_time = time.time()
        costs = [(position, movement_cost(position)) for position in positions]

        if current_time - self.note_last_time > self.NOTE_PAUSE_THRESHOLD:
            valid_positions = [pos for pos, cost in costs]
            self.last_three_notes = []
        else:
            valid_positions = [pos for pos, cost in costs if cost <= MAX_MOVEMENT_COST]

        if valid_positions and self.last_three_notes:
            result = min(valid_positions, key=movement_cost)
            if abs(string_names.index(result[0]) - string_names.index(self.last_three_notes[-1][0])) >= 3:
                return None
            return result
        elif valid_positions:
            return min(valid_positions, key=movement_cost)
        return None

    def update_last_three_notes(self, new_note):
        self.last_three_notes.append(new_note)
        if len(self.last_three_notes) > 3:
            self.last_three_notes.pop(0)

    def save_note_to_file(self, note, filename="output_tab.txt"):
        with open(filename, "a") as f:
            string, fret = note["position"]
            rel_start = note["start_time"] - self.start_offset
            f.write(f"{rel_start:.2f},{string},{fret}\n")

    def cleanup(self):
        if self.recording:
            self.recording = False
        if self.stream.is_active():
            self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
