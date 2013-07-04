# -*- coding:gbk -*-
import numpy as np

class syllable():
    '''音节类，f0_sequence是每一帧的f0形成的序列'''
    def __init__(self, begt='', endt='', f0_sequence=[], spk=""):
        if begt and endt and f0_sequence:
            self.begt = begt
            self.endt = endt
            self.f0_sequence = f0_sequence
            self.spk = spk  #这个音节的说话人
            self.zi = ""    #这个音节对应的拼音
    def __str__(self):
        return self.begt+' '+self.endt+' '+self.zi+' '+'spk:'+self.spk+' '+ \
            str(np.array(self.f0_sequence,dtype=np.float).mean())

class ROI():
    '''ROI类,左右各有一个音节,这里的ROI指的是大于200ms停顿处'''
    def __init__(self):
        self.LEFT = syllable()
        self.RIGHT = syllable()
        self.stt_roi = None
    def begt(self):
        '''返回interval的开始时间'''
        return self.LEFT.endt
    def endt(self):
        '''返回interval的结束时间'''
        return self.RIGHT.begt
    def __str__(self):
        return str(self.LEFT)+' '+str(self.RIGHT)

class spk_roi():
    '''这是存储某一个说话人在所有roi处的音节信息'''
    def __init__(self, spk=0, frame_seq=[]):
        self.spk = spk    #说话人
        self.frame_seq = frame_seq[:] #帧的序列,存储平滑之后的f0,把同一个说话人的每一帧都放进来
        self.avg = 0    #这个spk的f0平均值
        self.sd = 0     #这个spk的f0标准差
    def __str__(self):
        return 'speaker'+self.spk+' 均值 '+self.avg+' 标准差 ' + self.sd

class tone_roi():
    '''这是存储某一种tone在所有roi处的音节信息'''
    def __init__(self, tone='', frame_seq=[]):
        self.tone = tone    #音调,取值范围'1','2','3','4'
        self.frame_seq = frame_seq[:] #这地方一定要拷贝,不然之后修改这个序列时roi.LEFT.f0_sequence也变了
        self.avg = 0    
        self.sd = 0     
    def __str__(self):
        return 'tone'+self.tone+' 均值 '+self.avg+' 标准差 ' + self.sd