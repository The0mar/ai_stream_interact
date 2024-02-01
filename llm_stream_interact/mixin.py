import os
import cv2
import threading


class StreamerMixin:
    def __init__(self, cam_index):
        self._cam_index = cam_index
        self.cap = cv2.VideoCapture(self._cam_index)
        self._success, self._frame = self.cap.read()
        self._stopped = False

    def start_video_stream(self):
        threading.Thread(target=self._run, args=()).start()

    def _run(self):
        while not self._stopped:
            if not self._success:
                self._stop()
            else:
                self._ret, self._frame = self.cap.read()
                cv2.imshow("video", self._frame)
                if cv2.waitKey(1) == ord("q") & 0xFF:
                    self._stop()
                    self.cap.release()
                    cv2.destroyWindow("video")
                    os._exit(1)

    def _stop(self):
        self._stopped = True
