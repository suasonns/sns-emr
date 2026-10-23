from PIL import Image
import numpy as np
import sys

im = Image.open(sys.argv[1]).convert('RGBA')
arr = np.array(im)
h, w = arr.shape[:2]
alpha = arr[:, :, 3]
print("size", w, h)
print("alpha min/max", alpha.min(), alpha.max())


def row_segments(y):
    row = alpha[y] > 10
    segs = []
    in_seg = False
    start = 0
    for x in range(w):
        if row[x] and not in_seg:
            start = x
            in_seg = True
        elif not row[x] and in_seg:
            segs.append((start, x - 1))
            in_seg = False
    if in_seg:
        segs.append((start, w - 1))
    return segs


for y in range(0, h, 10):
    segs = row_segments(y)
    print(y, segs)
