import glob
import tempfile

import cv2
from PIL import Image


def _img_arrays_to_pil_imgs(frames):
    """ Writes cv np.array frames and reloads them in PIL.image format """
    with tempfile.TemporaryDirectory() as tmp:
        for n, frame in enumerate(frames):
            cv2.imwrite(f"{tmp}/frame{n}.jpg", frame)
        images_list = []
        image_paths = glob.glob(f"{tmp}/*.jpg")
        for path in image_paths:
            img = Image.open(path)
            images_list.append(img)
        return images_list
