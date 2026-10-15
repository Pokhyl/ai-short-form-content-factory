"""Offline geometry probe over saved original images; no provider calls."""
import json,itertools
from pathlib import Path
import cv2 as cv
import numpy as np
cv.setNumThreads(1)
root=Path('/data/checks/pixel-first-20261015')
receipt=json.loads((root/'receipt.json').read_text())
rows=[row for row in receipt['inspected'] if row['accepted']]
orb=cv.ORB_create(nfeatures=800,edgeThreshold=15,fastThreshold=7)
samples={}
for row in rows:
 path=Path(row['path']);path=path if path.is_absolute() else Path('/data')/path
 im=cv.imread(str(path))
 h,w=im.shape[:2];im=cv.resize(im,(round(w*min(1,512/max(w,h))),round(h*min(1,512/max(w,h)))),interpolation=cv.INTER_AREA)
 points,desc=orb.detectAndCompute(cv.cvtColor(im,cv.COLOR_BGR2GRAY),None)
 samples[row['asset_id']]=(im,points,desc)
results=[]
for left,right in itertools.combinations(samples,2):
 a,ka,da=samples[left];b,kb,db=samples[right]
 if da is None or db is None or min(len(da),len(db))<15:continue
 matches=[m for m,n in cv.BFMatcher(cv.NORM_HAMMING).knnMatch(da,db,k=2) if m.distance<0.70*n.distance and m.distance<50]
 if len(matches)<12:continue
 pa=np.float32([ka[m.queryIdx].pt for m in matches]);pb=np.float32([kb[m.trainIdx].pt for m in matches])
 cv.setRNGSeed(0)
 H,mask=cv.findHomography(pa,pb,cv.RANSAC,3.0)
 if H is None:continue
 good=mask.ravel().astype(bool);n=int(good.sum())
 if n<12:continue
 coverage=[cv.contourArea(cv.convexHull(p[good]))/(im.shape[0]*im.shape[1]) for p,im in ((pa,a),(pb,b))]
 warped=cv.warpPerspective(a,H,(b.shape[1],b.shape[0]))
 valid=cv.warpPerspective(np.ones(a.shape[:2],np.uint8),H,(b.shape[1],b.shape[0]))
 hull=np.zeros(b.shape[:2],np.uint8);cv.fillConvexPoly(hull,cv.convexHull(pb[good]).astype(np.int32),1)
 area=(valid>0)&(hull>0)
 x=warped[area].astype(float).ravel();y=b[area].astype(float).ravel()
 corr=float(np.corrcoef(x,y)[0,1]) if min(x.std(),y.std())>8 else 0
 results.append({'left':left,'right':right,'matches':len(matches),'inliers':n,'fraction':n/len(matches),'coverage':coverage,'correlation':corr})
(root/'geometry-probe.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
