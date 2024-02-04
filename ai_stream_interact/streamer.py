import os
import cv2
import threading


class Streamer:
    def __init__(self, cam_index):
        self._cam_index = cam_index
        self.cap = cv2.VideoCapture(self._cam_index)
        self._success, self._frame = self.cap.read()
        self._video_stream_is_stopped = True

    def start_video_stream(self):
        threading.Thread(target=self._run, args=()).start()

    def _run(self):
        self._video_stream_is_stopped = False
        while not self._video_stream_is_stopped:
            if not self._success:
                self._stop_video_stream()
            else:
                self._ret, self._frame = self.cap.read()
                cv2.imshow("video", self._frame)
                if cv2.waitKey(1) == ord("q") & 0xFF:
                    self.stop_video_stream()
                    self.cap.release()
                    cv2.destroyWindow("video")
                    os._exit(1)

    def stop_video_stream(self):
        self._video_stream_is_stopped = True
