"""Source-bound geometric identity for reframed/re-captioned photographs."""
import base64
import zlib


def describe(path):
    import cv2 as cv
    import numpy as np
    cv.setNumThreads(1)
    image = cv.imread(str(path))
    if image is None:
        raise ValueError('photo geometry decode failed')
    h, w = image.shape[:2]
    scale = min(1, 768 / max(w, h))
    image = cv.resize(image, (round(w * scale), round(h * scale)), interpolation=cv.INTER_AREA)
    h, w = image.shape[:2]
    points, descriptors = cv.SIFT_create(nfeatures=1500, contrastThreshold=0.01).detectAndCompute(
        cv.cvtColor(image, cv.COLOR_BGR2GRAY), None)
    points = points[:1500]
    raw = descriptors[:1500].astype(np.uint8).tobytes() if points else b''
    thumb = cv.resize(image, (256, 256), interpolation=cv.INTER_AREA)
    return {'algorithm': 'sift768-v1',
            'points': [[round(p.pt[0] / w, 6), round(p.pt[1] / h, 6)] for p in points],
            'descriptors': base64.b64encode(zlib.compress(raw)).decode(),
            'rgb256': base64.b64encode(zlib.compress(thumb.tobytes())).decode()}


def _unpack(value, limit):
    raw = base64.b64decode(value, validate=True)
    decoder = zlib.decompressobj()
    result = decoder.decompress(raw, limit + 1)
    if len(result) > limit or not decoder.eof or decoder.unused_data:
        raise ValueError('invalid bounded photo geometry data')
    return result


def decode(sample):
    import numpy as np
    if sample.get('algorithm') != 'sift768-v1':
        raise ValueError('unknown photo geometry algorithm')
    points = np.asarray(sample['points'], dtype=np.float32)
    if points.size == 0:
        points = points.reshape(0, 2)
    if (points.ndim != 2 or points.shape[1] != 2 or len(points) > 1500
            or not np.isfinite(points).all() or (points < 0).any() or (points > 1).any()):
        raise ValueError('invalid photo geometry points')
    descriptors = _unpack(sample['descriptors'], 1500 * 128)
    thumbnail = _unpack(sample['rgb256'], 256 * 256 * 3)
    if len(descriptors) != len(points) * 128 or len(thumbnail) != 256 * 256 * 3:
        raise ValueError('incomplete photo geometry data')
    return (points * 256, np.frombuffer(descriptors, np.uint8).reshape(-1, 128).astype(np.float32),
            np.frombuffer(thumbnail, np.uint8).reshape(256, 256, 3))


def same_view(left, right):
    import cv2 as cv
    import numpy as np
    cv.setNumThreads(1)
    pa, da, a = decode(left)
    pb, db, b = decode(right)
    if min(len(pa), len(pb)) < 24:
        return False
    matches = [m for m, n in cv.BFMatcher(cv.NORM_L2).knnMatch(da, db, k=2)
               if m.distance < 0.75 * n.distance and m.distance < 250]
    if len(matches) < 24:
        return False
    x = np.float32([pa[m.queryIdx] for m in matches])
    y = np.float32([pb[m.trainIdx] for m in matches])
    cv.setRNGSeed(0)
    transform, mask = cv.findHomography(x, y, cv.RANSAC, 1.2)
    if transform is None or not np.isfinite(transform).all():
        return False
    good = mask.ravel().astype(bool)
    if int(good.sum()) < 24 or float(good.mean()) < 0.5:
        return False
    # Shared logos, labels and small inset panels are not whole-photo identity.
    if min(cv.contourArea(cv.convexHull(p[good])) / (256 * 256) for p in (x, y)) < 0.4:
        return False
    warped = cv.warpPerspective(a, transform, (256, 256))
    valid = cv.warpPerspective(np.ones((256, 256), np.uint8), transform, (256, 256))
    hull = np.zeros((256, 256), np.uint8)
    cv.fillConvexPoly(hull, cv.convexHull(y[good]).astype(np.int32), 1)
    area = (valid > 0) & (hull > 0)
    left_pixels, right_pixels = warped[area].astype(float).ravel(), b[area].astype(float).ravel()
    if min(left_pixels.std(), right_pixels.std()) <= 8:
        return False
    return bool(np.corrcoef(left_pixels, right_pixels)[0, 1] >= 0.65)
