import glob
import tempfile
from typing import List

import cv2
import PIL
import numpy as np


def _img_arrays_to_pil_imgs(frames: np.ndarray) -> List[PIL.JpegImagePlugin.JpegImageFile]:
    """ Writes cv np.array frames and reloads them in PIL.image format """
    with tempfile.TemporaryDirectory() as tmp:
        for n, frame in enumerate(frames):
            cv2.imwrite(f"{tmp}/frame{n}.jpg", frame)
        images_list = []
        image_paths = glob.glob(f"{tmp}/*.jpg")
        for path in image_paths:
            img = PIL.Image.open(path)
            images_list.append(img)
        return images_list
