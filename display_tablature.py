import io
import fitz
import matplotlib.pyplot as plt
import pygame
import time

from PIL import Image


class TablatureRenderer:
    def __init__(self, pdf_filename, num_rows, max_notes_in_row):
        self.doc = fitz.open(pdf_filename)
        self.current_page = self.doc[0]
        self.fig, self.ax = plt.subplots(figsize=(15, 8))
        self.current_line = None
        self.num_rows = num_rows
        self.max_notes_in_row = max_notes_in_row
        self.current_row = 0
        print(self.fig.get)

        # Vertical spacing constants
        self.row_height = 50 / 378  # Height of each tablature row
        self.row_spacing = 30 / 378  # Space between rows
        self.top_margin = 62 / 378  # Space from top of plot

        # Calculate initial y positions
        self.set_axvline_ypos()
        self.last_note_time = 0

        # Will be set after first render
        self.plot_width = None
        self.plot_height = None
        self.get_plot_dimensions()
        print(self.plot_width, self.plot_height)

    def get_plot_dimensions(self):
        """Get the width and height from data coordinates"""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        self.plot_width = xlim[1] - xlim[0]
        self.plot_height = ylim[1] - ylim[0]
        return self.plot_width, self.plot_height

    def set_axvline_ypos(self):
        # Calculate the y positions for the current row
        row_start = self.top_margin + (self.current_row * (self.row_height + self.row_spacing))
        row_end = row_start + self.row_height

        self.ymin = 1 - row_end
        self.ymax = 1 - row_start

    def calculate_x_position(self, timestamp_index):
        # Calculate x position based on note index
        if timestamp_index >= self.max_notes_in_row:
            prev_row = self.current_row
            self.current_row = int(timestamp_index / self.max_notes_in_row)
            timestamp_index = timestamp_index % self.max_notes_in_row

            # Only update y positions if we've moved to a new row
            if prev_row != self.current_row:
                self.set_axvline_ypos()

        offset = 17
        scaling_factor = 36
        return timestamp_index * scaling_factor + offset

    def render_page(self):
        pix = self.current_page.get_pixmap()
        img_data = Image.open(io.BytesIO(pix.tobytes()))
        self.ax.clear()
        self.ax.imshow(img_data)
        self.ax.axis('off')
        self.fig.canvas.draw()

    def find_current_note(self, elapsed_time, note_metadata):
        # Find the current note being played by checking which time interval we're in
        for i in range(len(note_metadata)):
            current_time = note_metadata[i]
            next_time = note_metadata[i + 1] if i < len(note_metadata) - 1 else float('inf')

            if current_time <= elapsed_time < next_time:
                self.last_note_time = elapsed_time
                return i
        return None

    def update_line(self, elapsed_time, note_metadata):
        # Find and draw current note line
        current_note_idx = self.find_current_note(elapsed_time, note_metadata)

        if current_note_idx is not None:
            if self.current_line:
                self.current_line.remove()
            x_coord = self.calculate_x_position(current_note_idx)
            self.current_line = self.ax.axvline(x=x_coord, ymin=self.ymin, ymax=self.ymax, color='red', linestyle='--',
                                                alpha=0.7)
            self.fig.canvas.draw()


def play_audio_with_tablature(filename_audio, tablature_renderer, note_metadata):
    pygame.mixer.init()
    pygame.mixer.music.load(filename_audio)

    # Display the initial PDF
    tablature_renderer.render_page()
    plt.pause(0.5)  # Small pause to ensure the window is ready

    # Start playing audio
    pygame.mixer.music.play()
    start_time = time.time()

    try:
        while pygame.mixer.music.get_busy():
            elapsed_time = time.time() - start_time
            tablature_renderer.update_line(elapsed_time, note_metadata)
            plt.pause(0.001)  # Small pause to prevent high CPU usage
    except KeyboardInterrupt:
        pygame.mixer.music.stop()
    finally:
        # Clean up
        if tablature_renderer.current_line:
            tablature_renderer.current_line.remove()
        tablature_renderer.fig.canvas.draw()


def main():
    filename_pdf = "final_tablature.pdf"
    filename_audio = "output_audio.wav"
    note_metadata_file = "output_tab.txt"
    max_notes_in_row = 22

    # Read note timestamps
    note_timestamps = []
    with open(note_metadata_file) as notes:
        for note in notes:
            note_timestamps.append(float(note.split(",")[0]))
    num_rows = int(len(note_timestamps) / max_notes_in_row)
    print(len(note_timestamps))
    print(num_rows)
    # Create renderer and start playback
    renderer = TablatureRenderer(filename_pdf, num_rows, max_notes_in_row)
    play_audio_with_tablature(filename_audio, renderer, note_timestamps)
    plt.show()  # Keep the window open until closed by user


if __name__ == "__main__":
    main()
