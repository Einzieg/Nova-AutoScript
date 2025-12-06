import cv2
import numpy as np


class ImageTools:

    def __init__(self):
        pass

    @staticmethod
    def apply_mask(image: cv2.Mat, mask_def: dict) -> cv2.Mat:
        """Apply to retain/remove mask rules to image and return result.

        Behavior:
        - If mask_def contains any 'retain' rectangles, start from a black canvas and copy those regions from image.
        - If mask_def has no 'retain', start from the original image (so only 'remove' will black out areas).
        - Then apply 'remove' rectangles to set those regions to black in the result (override retain if overlapping).

        Rectangles are tuples (x1,y1,x2,y2). Coordinates are clamped to image bounds.
        """
        h, w = image.shape[:2]
        has_retain = bool(mask_def.get('retain'))

        if has_retain:
            out = np.zeros_like(image)

            for (x1, y1, x2, y2) in mask_def.get('retain', ()):
                xs, xe = max(0, min(x1, x2)), min(w, max(x1, x2))
                ys, ye = max(0, min(y1, y2)), min(h, max(y1, y2))
                if xs < xe and ys < ye:
                    out[ys:ye, xs:xe] = image[ys:ye, xs:xe]
        else:
            out = image.copy()

        for (x1, y1, x2, y2) in mask_def.get('remove', ()):
            xs, xe = max(0, min(x1, x2)), min(w, max(x1, x2))
            ys, ye = max(0, min(y1, y2)), min(h, max(y1, y2))
            if xs < xe and ys < ye:
                out[ys:ye, xs:xe] = 0

        return out
