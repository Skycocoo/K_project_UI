# -*- coding: utf-8 -*-
"""
Created on Fri Jul 14 15:59:06 2017

@author: medialab
"""

import cv2
import cPickle,h5py
import ctypes
import glob,os
from Mocam2Kinect import *
from Human_mod import *
from rawK2array import *
from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime
import numpy as np

vid_src  = 'E:/avi/Angela.lnk_Angela_data0306090752_ex4.avi'
name    = 'Angela_data0306090752_ex4'
dst_path = 'E:/frame/'+name+'/'

Kinfile  = 'D:/Project/K_project/data/Motion and Kinect raw data/20170306/pkl/Angela/Angela_data0306090752_ex4.pkl'
Minfile  = 'D:/Project/K_project/data/1216/Andy_2016-12-15 04.15.27 PM_FPS30_motion.pkl'
Mpinfile = 'D:/AllData_0327(0712)/AllData_0327/GPRresult/K2M_800/Andy_data201612151615_unified_ex4.h5'


if not os.path.exists(dst_path):
    os.makedirs(dst_path)



#  Joints  initialize
kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body|PyKinectV2.FrameSourceTypes_Depth|PyKinectV2.FrameSourceTypes_BodyIndex)       
joints = ctypes.POINTER(PyKinectV2._Joint)
joints_capacity = ctypes.c_uint(PyKinectV2.JointType_Count)
joints_data_type = PyKinectV2._Joint * joints_capacity.value
joints = ctypes.cast(joints_data_type(), ctypes.POINTER(PyKinectV2._Joint))

jidx = [0,1,2,3,4,5,6,8,9,10,20]
jidx_draw = [4,5,6,8,9,10]

color = {}
color[4 ]     =(255,0,0)
color[5 ]     =(255,255,0)
color[6 ]     =(0,0,255)
color[8 ]     =(255,0,255)
color[9 ]     =(0,255,255)
color[10]     =(0,255,0)
color['bone'] = (50,200,50)



kdata   = rawK2ary(cPickle.load(file(Kinfile,'r')),jidx)
kdata2D = rawK2ary2D(cPickle.load(file(Kinfile,'r')),jidx)
mdata   = cPickle.load(file(Minfile,'r'))

if Mpinfile.split('/')[-1][-1] == 'l' :
    mpdata = cPickle.load(file(Mpinfile,'r'))
    Len   = min(mpdata['rcpos'].shape[1],kdata[0].shape[1])    
else:    
    mpdata = h5py.File(Mpinfile)['data'][:]
    Len   = min(mpdata.shape[1],kdata[0].shape[1])



Ccord = {}
for i in jidx:
    Ccord[i] = np.zeros((2,Len))
    
cv2.waitKey(50000) 

pos_Kinect = Mocam2Kinect(mdata) 


data = mpdata.reshape(-1,3,mpdata.shape[1])
Pos_Unified = human_mod_unified_Mocam(pos_Kinect,data,kdata[4],kdata[8],Len)


for frame_idx in range(Len):
    for j in jidx_draw:

        joints[j].Position.x = Pos_Unified[j][0,frame_idx] 
        joints[j].Position.y = Pos_Unified[j][1,frame_idx] 
        joints[j].Position.z = Pos_Unified[j][2,frame_idx] 

    Jps = kinect.body_joints_to_color_space(joints)    
    for jj in jidx_draw:
        Ccord[jj][0,frame_idx] = Jps[jj].x
        Ccord[jj][1,frame_idx] = Jps[jj].y


print Ccord[4]


#FPS = 30
#Fsize = (1920,1080) #frame size
#video = cv2.VideoWriter('GPRM2K_KandM.avi', -1, FPS, Fsize)
#for idx,imgfile in enumerate(glob.glob(os.path.join('../data/frame/','*.jpg'))):
#    print idx
#    img  = cv2.imread(imgfile)
#    imgk = cv2.imread(imgfile)
#    for i in jidx_draw:
#        cv2.circle(img ,(int(Ccord[i][0,idx]),int(Ccord[i][1,idx])), 5, (0,0,255), -1)
#        cv2.circle(img ,(int(kdata2D[i][0,idx]),int(kdata2D[i][1,idx])), 5, (0,255,0), -1)
#
#    cv2.line(img,(int(Ccord[4][0,idx]),int(Ccord[4][1,idx])),(int(Ccord[5][0,idx]) ,int(Ccord[5][1,idx])) ,(0,0,255),3) 
#    cv2.line(img,(int(Ccord[5][0,idx]),int(Ccord[5][1,idx])),(int(Ccord[6][0,idx]) ,int(Ccord[6][1,idx])) ,(0,0,255),3)
#    cv2.line(img,(int(Ccord[9][0,idx]),int(Ccord[9][1,idx])),(int(Ccord[8][0,idx]) ,int(Ccord[8][1,idx])) ,(0,0,255),3)
#    cv2.line(img,(int(Ccord[9][0,idx]),int(Ccord[9][1,idx])),(int(Ccord[10][0,idx]),int(Ccord[10][1,idx])),(0,0,255),3)
#
#    cv2.line(img,(int(kdata2D[4][0,idx]),int(kdata2D[4][1,idx])),(int(kdata2D[5][0,idx]) ,int(kdata2D[5][1,idx])) ,(0,255,0),3) 
#    cv2.line(img,(int(kdata2D[5][0,idx]),int(kdata2D[5][1,idx])),(int(kdata2D[6][0,idx]) ,int(kdata2D[6][1,idx])) ,(0,255,0),3)
#    cv2.line(img,(int(kdata2D[9][0,idx]),int(kdata2D[9][1,idx])),(int(kdata2D[8][0,idx]) ,int(kdata2D[8][1,idx])) ,(0,255,0),3)
#    cv2.line(img,(int(kdata2D[9][0,idx]),int(kdata2D[9][1,idx])),(int(kdata2D[10][0,idx]),int(kdata2D[10][1,idx])),(0,255,0),3)
#    
#    video.write(img)
#
#del video




vid      = cv2.VideoCapture(vid_src)

idx = 0

while idx<Len:
    print idx
    ret, img = vid.read()
    
    for i in jidx_draw:
        cv2.circle(img ,(int(Ccord[i][0,idx]),int(Ccord[i][1,idx])), 5, (0,0,255), -1)
        cv2.circle(img ,(int(kdata2D[i][0,idx]),int(kdata2D[i][1,idx])), 5, (0,255,0), -1)

    cv2.line(img,(int(Ccord[4][0,idx]),int(Ccord[4][1,idx])),(int(Ccord[5][0,idx]) ,int(Ccord[5][1,idx])) ,(0,0,255),3) 
    cv2.line(img,(int(Ccord[5][0,idx]),int(Ccord[5][1,idx])),(int(Ccord[6][0,idx]) ,int(Ccord[6][1,idx])) ,(0,0,255),3)
    cv2.line(img,(int(Ccord[9][0,idx]),int(Ccord[9][1,idx])),(int(Ccord[8][0,idx]) ,int(Ccord[8][1,idx])) ,(0,0,255),3)
    cv2.line(img,(int(Ccord[9][0,idx]),int(Ccord[9][1,idx])),(int(Ccord[10][0,idx]),int(Ccord[10][1,idx])),(0,0,255),3)

    cv2.line(img,(int(kdata2D[4][0,idx]),int(kdata2D[4][1,idx])),(int(kdata2D[5][0,idx]) ,int(kdata2D[5][1,idx])) ,(0,255,0),3) 
    cv2.line(img,(int(kdata2D[5][0,idx]),int(kdata2D[5][1,idx])),(int(kdata2D[6][0,idx]) ,int(kdata2D[6][1,idx])) ,(0,255,0),3)
    cv2.line(img,(int(kdata2D[9][0,idx]),int(kdata2D[9][1,idx])),(int(kdata2D[8][0,idx]) ,int(kdata2D[8][1,idx])) ,(0,255,0),3)
    cv2.line(img,(int(kdata2D[9][0,idx]),int(kdata2D[9][1,idx])),(int(kdata2D[10][0,idx]),int(kdata2D[10][1,idx])),(0,255,0),3)

  
    fname =dst_path + name+'_'+repr(idx).zfill(4)+'.jpg'

    cv2.imwrite(fname,img)
    
    idx +=1
    
vid.release()
    






