# -*- coding:gbk -*-
import numpy as np

class syllable():
    '''�����࣬f0_sequence��ÿһ֡��f0�γɵ�����'''
    def __init__(self, begt='', endt='', f0_sequence=[], spk=""):
        if begt and endt and f0_sequence:
            self.begt = begt
            self.endt = endt
            self.f0_sequence = f0_sequence
            self.spk = spk  #������ڵ�˵����
            self.zi = ""    #������ڶ�Ӧ��ƴ��
    def __str__(self):
        return self.begt+' '+self.endt+' '+self.zi+' '+'spk:'+self.spk+' '+ \
            str(np.array(self.f0_sequence,dtype=np.float).mean())

class ROI():
    '''ROI��,���Ҹ���һ������,�����ROIָ���Ǵ���200msͣ�ٴ�'''
    def __init__(self):
        self.LEFT = syllable()
        self.RIGHT = syllable()
        self.stt_roi = None
    def begt(self):
        '''����interval�Ŀ�ʼʱ��'''
        return self.LEFT.endt
    def endt(self):
        '''����interval�Ľ���ʱ��'''
        return self.RIGHT.begt
    def __str__(self):
        return str(self.LEFT)+' '+str(self.RIGHT)

class spk_roi():
    '''���Ǵ洢ĳһ��˵����������roi����������Ϣ'''
    def __init__(self, spk=0, frame_seq=[]):
        self.spk = spk    #˵����
        self.frame_seq = frame_seq[:] #֡������,�洢ƽ��֮���f0,��ͬһ��˵���˵�ÿһ֡���Ž���
        self.avg = 0    #���spk��f0ƽ��ֵ
        self.sd = 0     #���spk��f0��׼��
    def __str__(self):
        return 'speaker'+self.spk+' ��ֵ '+self.avg+' ��׼�� ' + self.sd

class tone_roi():
    '''���Ǵ洢ĳһ��tone������roi����������Ϣ'''
    def __init__(self, tone='', frame_seq=[]):
        self.tone = tone    #����,ȡֵ��Χ'1','2','3','4'
        self.frame_seq = frame_seq[:] #��ط�һ��Ҫ����,��Ȼ֮���޸��������ʱroi.LEFT.f0_sequenceҲ����
        self.avg = 0    
        self.sd = 0     
    def __str__(self):
        return 'tone'+self.tone+' ��ֵ '+self.avg+' ��׼�� ' + self.sd