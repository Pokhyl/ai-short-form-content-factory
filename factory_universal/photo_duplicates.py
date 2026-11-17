"""Crop/resize resistant source-photo deduplication; no learned model."""
import cv2
import numpy as np
from PIL import Image,ImageOps

cv2.setNumThreads(1)

def fingerprint(path):
 with Image.open(path) as source:
  image=ImageOps.exif_transpose(source).convert('RGB');image.thumbnail((960,960),Image.Resampling.LANCZOS)
  gray=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2GRAY)
 detector=cv2.ORB_create(nfeatures=900,fastThreshold=10,edgeThreshold=16)
 keypoints,descriptors=detector.detectAndCompute(gray,None)
 points=np.asarray([point.pt for point in keypoints],dtype=np.float32).reshape((-1,2))
 return {'gray':gray,'points':points,'descriptors':descriptors}

def duplicate(left,right):
 one=left['descriptors'];two=right['descriptors']
 result={'duplicate':False,'matches':0,'inliers':0}
 if one is None or two is None or min(len(one),len(two))<16:return result
 pairs=cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(one,two,k=2)
 matches=[pair[0] for pair in pairs if len(pair)==2 and pair[0].distance<=42 and pair[0].distance<.72*pair[1].distance]
 unique={}
 for match in sorted(matches,key=lambda row:row.distance):unique.setdefault(match.trainIdx,match)
 matches=list(unique.values());result['matches']=len(matches)
 if len(matches)<16:return result
 source=np.asarray([left['points'][match.queryIdx] for match in matches])
 target=np.asarray([right['points'][match.trainIdx] for match in matches])
 cv2.setRNGSeed(0)
 transform,mask=cv2.estimateAffinePartial2D(source,target,method=cv2.RANSAC,ransacReprojThreshold=2.5,maxIters=2000,confidence=.995)
 if transform is None or mask is None:return result
 inliers=mask.ravel().astype(bool);count=int(inliers.sum());result['inliers']=count
 if count<16 or count/len(matches)<.7:return result
 def coverage(points,image):
  return float(cv2.contourArea(cv2.convexHull(points)))/max(1,image.shape[0]*image.shape[1])
 first=coverage(source[inliers],left['gray']);second=coverage(target[inliers],right['gray'])
 result['coverage']=[round(first,4),round(second,4)]
 if max(first,second)<.35 or min(first,second)<.04:return result
 height,width=right['gray'].shape
 projected=cv2.warpAffine(left['gray'],transform,(width,height))
 overlap=cv2.warpAffine(np.ones_like(left['gray'],dtype=np.uint8),transform,(width,height),flags=cv2.INTER_NEAREST).astype(bool)
 if int(overlap.sum())<1000:return result
 a=cv2.GaussianBlur(projected,(5,5),1)[overlap].astype(np.float32);b=cv2.GaussianBlur(right['gray'],(5,5),1)[overlap].astype(np.float32)
 if min(float(a.std()),float(b.std()))<8:return result
 correlation=float(np.corrcoef(a,b)[0,1]);result['correlation']=round(correlation,5)
 result['duplicate']=correlation>=.97
 return result
