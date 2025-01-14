import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button

from AudioProcessor import AudioProcessor
from TablatureVisualizer import TablatureVisualizer


class GuitarRecorder:
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.visualizer = TablatureVisualizer()
        self.is_recording = False

        # Create figure and button
        self.visualizer.fig.subplots_adjust(bottom=0.2)  # Make room for button
        self.button_ax = self.visualizer.fig.add_axes([0.7, 0.05, 0.15, 0.075])
        self.stop_button = Button(self.button_ax, 'Stop Recording')
        self.stop_button.on_clicked(self.stop_recording)
        self.duration = 60  # 60 second time limit

    def start(self):
        self.is_recording = True
        # Start audio processing
        self.audio_thread = threading.Thread(
            target=self.audio_processor.start_recording,
            args=(self.duration,)
        )
        self.audio_thread.start()

        # Start visualization
        self.ani = animation.FuncAnimation(
            self.visualizer.fig,
            self.update_frame,
            interval=50,
            blit=True
        )
        plt.show()

    def update_frame(self, frame):
        if not self.is_recording:
            # self.cleanup()
            plt.close()
            return self.visualizer.marker, *[line for tab in self.visualizer.tab_lines for line in tab]
        return self.visualizer.update_plot(frame)

    def stop_recording(self, event=None):
        print("Stopping recording...")
        self.is_recording = False
        self.audio_processor.recording = False
        self.visualizer.running = False

    def cleanup(self):
        self.audio_processor.cleanup()
        self.visualizer.save_tablature_pdf()


def main():
    recorder = GuitarRecorder()
    try:
        recorder.start()
    except KeyboardInterrupt:
        print("\nStopping recording and visualization...")
        recorder.stop_recording()
    finally:
        recorder.cleanup()


if __name__ == "__main__":
    main()
