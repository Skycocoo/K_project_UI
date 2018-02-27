import numpy as np
from scipy.signal import argrelextrema
from scipy.ndimage.filters import gaussian_filter as gf_2D
from scipy.ndimage.filters import gaussian_filter1d as gf
import pdb

class Breath_status(object):
    """ detect breathing status
    """
    def __init__(self):
        self.ref_bdry      = np.array([])
        self.ref_dmap      = None
        self.breath_list   = []
        self.breath        = None
        self.ngframe       = []
        self.brthtype      = 'out'
        self.missingbreath = []
        self.ana_ary       = []
        self.max_ary       = np.array([[0, np.inf]])
        self.min_ary       = np.array([[0, -np.inf]])
        self.cnt_max_flag  = False
        self.cnt_min_flag  = False
        self.cnt_max       = 0 
        self.cnt_min       = 0      
        self.max_len       = 0
        self.min_len       = 0
        self.plot_flag     = False
        self.brth_in_flag  = False
        self.first_flag    = True
        # default parameters
        self.do      = False
        self.err     = []
        self.evalstr = ''

    def rm_pulse(self, ary, th=10):
        """ remove small pulse in the binary array
        """
        split_ary = np.split(ary, np.where(np.diff(ary)!=0)[0]+1)
        ary_len = [len(a) for a in split_ary]
        merge_idx = np.where(np.array(ary_len) < th)[0]
        if len(merge_idx) > 0:
            ary_idx = [sum(ary_len[:i]) for i in xrange(1, len(ary_len))]
            ary_idx.append(len(ary))
            for i in merge_idx:
                if i == 0:
                    ary[:ary_idx[i]] = ary[ary_idx[i]]
                else:
                    ary[ary_idx[i-1]:ary_idx[i]] = ary[ary_idx[i-1]-1]
        return ary

    def breathextract(self, bdry, dmap):
        """according to the depth map in the chest region,
           detect breath in and breath out.
        """
        cur_bdry = np.array([bdry[0][1], bdry[3][1], bdry[1][0], bdry[2][0]])
        if len(self.ref_bdry) == 0:
            # setup reference frame's boundary (up, down, left and right)
            self.ref_bdry = cur_bdry
            self.ref_dmap = dmap
        else:
            ubdry = np.array([int(min(cur_bdry[0], self.ref_bdry[0])),
                              int(max(cur_bdry[1], self.ref_bdry[1])),
                              int(max(cur_bdry[2], self.ref_bdry[2])),
                              int(min(cur_bdry[3], self.ref_bdry[3]))])
            blk_diff = gf_2D((dmap.astype(float)-self.ref_dmap.astype(float))[ubdry[1]:ubdry[0], ubdry[2]:ubdry[3]], 5)
            self.breath_list.append(np.mean(blk_diff))

    def breath_analyze(self, offset=0, th=10):
        """ Analyze the human and breath in/out behavior  
        """
        self.do = True
        # breath part
        breath_gd = np.gradient(gf(self.breath_list, 10))
        breath_gd[breath_gd > 0] = 1
        breath_gd[breath_gd < 0] = 0
        breath_gd = self.rm_pulse(breath_gd)
        breath_pulse = breath_gd[:-1]-np.roll(breath_gd, -1)[:-1]
        breath_out = argrelextrema(breath_pulse, np.less, order=10)[0]#+offset  # endpoint of each b out
        breath_in = argrelextrema(breath_pulse, np.greater, order=10)[0]#+offset # endpoint of each b in
        self.breath = np.sort(np.hstack([breath_in, breath_out, len(self.breath_list)-1]))

        if self.breath[0] == breath_in[0]:
            self.brthtype = 'in'
        else:
            self.brthtype = 'out'
        print('breath '+self.brthtype+' from frame '+str(0)+' to frame '+str(self.breath[0]))

        b_in = []
        b_out = []
        delidx = []

        if len(self.breath) != 0:       
            for i, j in zip(self.breath[:-1], self.breath[1:]):
                breath_diff = self.breath_list[j]-self.breath_list[i]
                if abs(breath_diff) > 3000:  # really breath in/out
                    if abs(breath_diff) < 30000:  # not deep breath
                        if breath_diff < 0:  # breath out
                            print('breath out from frame '+str(i)+' to frame '+str(j)
                                +' <== breath not deep enough')
                            b_out.append(j-i)
                            self.ngframe.append(i)
                        else:  # breath in
                            print('breath in from frame '+str(i)+' to frame '+str(j)
                            +' <== breath not deep enough')
                            b_in.append(j-i)
                            self.ngframe.append(i)
                    else: 
                        if breath_diff > 0:  # breath out
                            print('breath out from frame '+str(i)+' to frame '+str(j))
                            b_out.append(j-i)
                        else:  # breath in
                            print('breath in from frame '+str(i)+' to frame '+str(j))
                            b_in.append(j-i)
                else:
                    delidx.append(np.argwhere(self.breath==j)[0][0])
            if len(delidx) > 0:
                self.breath = np.delete(self.breath, np.array(delidx))
            print('\naverage breath out freq is: '+str(np.round(30./np.mean(b_out), 2))+' Hz')
            print('\naverage breath in freq is: '+str(np.round(30./np.mean(b_in), 2))+' Hz')
        else:
            raise ImportError('Doing too fast !! please redo again !!')

    def brth_hand_sync(self, lhopen, lhclose):
        """calculate breath and hand open/close relation
        """
        hand = np.sort(np.hstack([lhopen, lhclose]))
        if self.breath[0] == 0:
            breath_data = self.breath[1:]
        else:
            breath_data = self.breath
        if hand[0] == lhopen[0]:  # first term is open
            mode = 'open'
        else:
            mode = 'close'

        hand_trunc = np.vstack([hand, np.roll(hand, -1)])[:,:-1].T
        hand_trunc = np.vstack([hand_trunc, np.array([hand[-1], len(self.breath_list)-1])])

        if mode == 'close':
            hand_trunc_close = hand_trunc[::2,:]
            hand_trunc_open = hand_trunc[1::2,:]
        else:
            hand_trunc_close = hand_trunc[1::2,:]
            hand_trunc_open = hand_trunc[::2,:]            

        if self.brthtype == 'out':
            breath_in = breath_data[1::2]
            breath_out = breath_data[::2]
            if abs(breath_out[0]-hand_trunc_open[0, 0]) < 10:
                breath_out[0] =  hand_trunc_open[0, 0]            
        else:
            breath_in = breath_data[::2]
            breath_out = breath_data[1::2]
            if abs(breath_in[0]-hand_trunc_close[0, 0]) < 10:
                breath_in[0] =  hand_trunc_close[0, 0]
                   
        hand_chk = np.ones(len(hand_trunc))
        # print hand_trunc
        cnt = 0
        for idx, i in enumerate(breath_in):
            loc = np.where(((i >= hand_trunc_close[:, 0]) & (i <= hand_trunc_close[:, 1])) == True)[0]
            if len(loc) == 1:
                cnt += 1
                if (2*loc) < len(hand_trunc):
                   hand_chk[2*loc] = 0 
            elif len(loc) == 0:
                pass
            else:
                print hand_trunc
        for idx, i in enumerate(breath_out):
            loc = np.where(((i >= hand_trunc_open[:, 0]) & (i <= hand_trunc_open[:, 1])) == True)[0]
            if len(loc) == 1:
                cnt += 1
                if (2*loc) < len(hand_trunc):
                   hand_chk[2*loc+1] = 0                 
            elif len(loc) == 0:
                pass
            else:
                print hand_trunc
        self.missingbreath = hand_trunc[hand_chk==1]

        sync_rate = cnt*1./len(hand_trunc)*100
        print('hand and breath synchronize rate is '+str(np.round(sync_rate, 2))+'%')

    def local_minmax(self, seq1, seq2, th, minmax_str, rng=15):
        """ finding local min or max depending on the argument minmax
        """
        breath_list = gf(self.breath_list, 3)
        if minmax_str == 'min':
            minmax = np.less
        elif minmax_str == 'max':
            minmax = np.greater        
        pts = argrelextrema(breath_list, minmax, order=rng)[0]
        if len(pts) != 0:
            if pts[-1] - seq1[-1][0] >= rng and minmax(breath_list[pts[-1]], th)\
                and pts[-1] > seq2[-1, 0]:
                seq1 = np.vstack((seq1, np.array([pts[-1], breath_list[pts[-1]]])))
            elif 0 < pts[-1]-seq1[-1][0] < rng and minmax(breath_list[pts[-1]], seq1[-1][1]):
                seq1[-1] = np.array([pts[-1], breath_list[pts[-1]]])
        return np.atleast_2d(seq1)
        
    def detect_brth(self, rng=10):

        if self.brth_in_flag:
            self.max_ary = self.local_minmax(self.max_ary, self.min_ary, self.min_ary[-1, 1]+10, 'max')
            if self.max_ary.shape[0] > self.max_len:
                self.cnt_max_flag = True
            if self.cnt_max_flag:
                self.cnt_max += 1
            if self.cnt_max == rng:
                self.cnt_max = 0
                self.cnt_max_flag = False
                print ('find one max  ' +str(self.max_ary[-1,0]))
                self.brth_in_flag = False
                time = (np.atleast_2d(self.max_ary[-1, 0])-np.atleast_2d(self.min_ary[-1, 0]))/30
                print('breath out takes time = '+str(time[0]))
                self.ana_ary.append([self.max_ary[-1, 0], 1, self.max_ary[-1, 1]])
        # detect brth in
        else:
            self.min_ary = self.local_minmax(self.min_ary, self.max_ary, self.max_ary[-1, 1]-10, 'min')
            if self.min_ary.shape[0] > self.min_len:
                self.cnt_min_flag = True
            if self.cnt_min_flag:
                self.cnt_min += 1
            if self.cnt_min == rng:
                self.cnt_min = 0
                self.cnt_min_flag = False
                print ('find one min ' + str(self.min_ary[-1, 0]))
                self.brth_in_flag = True
                if self.first_flag:
                    self.first_flag = False
                else:
                    time = (np.atleast_2d(self.min_ary[-1, 0])-np.atleast_2d(self.max_ary[-1, 0]))/30
                    print('breath in takes time = '+str(time[0]))
                    self.ana_ary.append([self.min_ary[-1, 0], 0, self.min_ary[-1, 1]])        
                    if np.abs(self.max_ary[-1, 1] - self.min_ary[-1, 1]) < 40 :
                        print('breath in not deep enough '+str(np.abs(self.max_ary[-1, 1] - self.min_ary[-1, 1])))             
        self.max_len = self.max_ary.shape[0]
        self.min_len = self.min_ary.shape[0]

    def run(self, bdry, dmap):
        self.breathextract(bdry, dmap)
        self.detect_brth()

        