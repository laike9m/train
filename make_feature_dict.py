# -*- coding:gbk -*-

import os
import pickle
import re
from math import ceil
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster import vq
from collections import OrderedDict
from collections import deque
from defination import *

def time_cmp(sgm_time,stt_time):
    '''��sgm��,������ֵ��stt�󷵻ظ�ֵ.����ʱ�䶼��str����'''
    stt_time_list = stt_time.split(':')
    stt = 0
    if len(stt_time_list) == 2:
        stt = float(stt_time_list[0])*60 + float(stt_time_list[1])
    if len(stt_time_list) == 3:
        stt = float(stt_time_list[0])*3600 + float(stt_time_list[1])*60 \
                   + float(stt_time_list[2])
    sgm = float(sgm_time)
    return sgm - stt    #����float

def read_sgm(sgm_lines):
    '''
        ��sgm�ļ��ж�ȡ��Ϣ,������˵
        ���һ��������Ķ�����:
    <section type=report startTime=1560.100 endTime=1590.672>
        ������Ķ�����:
    <section type=nontrans startTime=1590.672 endTime=1920.000>
        ֻҪ�ҵ����һ��type��report�Ķ��伴��,�öεĽ���ʱ����ǽضϵ�ʱ��
        ���������getpitch��Ҳ��,���������һ��
    '''
    section_lines = [l for l in sgm_lines if l.startswith('<section')]
    section_lines.reverse()
    for l in section_lines:
        if re.search('type=report',l):#���һ��������Ķ�
            endt = re.search(r"(?<=endTime=)[\d.]*",l).group()
            return endt #�������һ�����������Ľ���ʱ��
    


def main(nontrans,kmeans):
    '''��ں���'''
    maindir = '..\wav_processing\output\\'
    csdir = '..\LexicalChain\chainstrength\\'
    simdir = '..\Texttiling\similarity\\'
    pitchdir = '..\Pitch\output\\'
    sgmfiles = [f for f in os.listdir(maindir) if f.endswith('sgm')]
    sttfiles = [f for f in os.listdir(maindir) if f.endswith('stt')]
    resfiles = [f for f in os.listdir(maindir) if f.endswith('res')]
    w_cs = 40   #chainstrength α���ӳ���
    w_s = 20    #similarity α���ӳ���
    if os.path.exists('boundary_deserted.txt'):
        os.remove('boundary_deserted.txt')
    
    for (sgmfile,sttfile,resfile) in zip(sgmfiles[:25],sttfiles[:25],resfiles[:25]):
        print(sgmfile,sttfile,resfile)
        sgm = open(maindir+sgmfile)
        stt = open(maindir+sttfile)
        res = open(maindir+resfile)
        stt_lines = stt.readlines()
        sgm_lines = sgm.readlines()
        res_lines = res.readlines()

        sgm_meaninful_end = read_sgm(sgm_lines)   #���һ��report����Ľ���ʱ��
        
        #�γ�stt��[[begt1,endt1],[begt2,endt2]]
        stt_timeline = []
        for line in stt_lines:
            obj = re.search(r'(?<=begt=)([^ ]+).*(?<=endt=)([^ ]+)',line)
            if obj:
                if time_cmp(sgm_meaninful_end, obj.group(1)) > 0:
                    t = [obj.group(1),obj.group(2)]
                    stt_timeline.append(t)
        
        #�γ�stt_roi_list:[(begt1,endt1),(begt2,endt2)],���Ѿ�������roi��
        stt_roi_list = []
        train = []
        for i in range(len(stt_timeline)-1):
            stt_roi_list.append((stt_timeline[i][1],stt_timeline[i+1][0]))
            d = {'roi_begt':stt_timeline[i][1],'roi_endt':stt_timeline[i+1][0], \
                 'isboundary':0,'isnon':0}
            d = OrderedDict(sorted(list(d.items())))
            train.append(d)
                
        sgm_timeline = []      #����sgm������ʼ/����ʱ��,��������nontrans��  
        if nontrans == 'include':
            for line in sgm_lines:
                if line.startswith('<section'):
                    obj = re.search(r'(?<=startTime=)([^ ]+).*(?<=endTime=)([\d.]+)',line)
                    if obj:
                        t = (obj.group(1),obj.group(2))
                        sgm_timeline.append(t)
        else:
            for line in sgm_lines:
                if line.startswith('<section') and 'nontrans' not in line:
                    obj = re.search(r'(?<=startTime=)([^ ]+).*(?<=endTime=)([\d.]+)',line)
                    if obj:
                        t = (obj.group(1),obj.group(2))
                        sgm_timeline.append(t)
            
                
        for t_sgm in sgm_timeline[1:]:  #��sgm boundary��Ӧ��stt_roi
            smallest = 1000000
            for t_stt in stt_roi_list:
                delta1 = abs(time_cmp(t_sgm[0],t_stt[0]))
                delta2 = abs(time_cmp(t_sgm[0],t_stt[1]))
                delta = delta1 if delta1<delta2 else delta2
                if smallest > delta:
                    smallest = delta
                else:
                    train[stt_roi_list.index(t_stt)-1]['isboundary'] = 1
                    break   #delta��ʼ����,˵����һ���������ʱ���,���roi���Ǳ߽�    
        
        seg_info = []   #����seg_info,��get_chain����seg_info��ͬ���Ķ���
        stt_block_start = [d['roi_endt'] for d in train if d['isboundary']]
        stt_block_start.insert(0, stt_timeline[0][0])#�����һ��stt���ӵ���ʼʱ��
        ziseq_of_utt = []   #ÿ�����ӵ�������,['������...','������...',]
        for line in stt_lines:#����seg_info
            match = re.search(r'(?<=zi=)[^ ]*',line)
            obj = re.search(r'(?<=begt=)([^ ]+).*(?<=endt=)([^ ]+)',line)
            if match and obj:
                ziseq_of_utt.append(match.group())
                begt = obj.group(1)
                if begt in stt_block_start:#�Ƕ��俪ʼ
                    new_segment = {}
                    new_segment['begt'] = begt
                    new_segment['zi'] = ''
                    new_segment['zi'] += match.group()
                    new_segment['length'] = len(new_segment['zi'])
                    seg_info.append(new_segment)
                else:
                    seg_info[-1]['zi'] += match.group()
                    seg_info[-1]['length'] = len(seg_info[-1]['zi'])
        
        zi_accumulate = []  #ÿ�仰�����ֶ�Ӧstt�еĵڼ�����,�ۻ�
        for ziseq in ziseq_of_utt:
            if len(zi_accumulate) == 0:
                zi_accumulate.append(len(ziseq))
            else:
                zi_accumulate.append(zi_accumulate[-1]+len(ziseq))
            
        for d,zi_index in zip(train, zi_accumulate):#train���zi_index��
            d['zi_index'] = zi_index
        
        
        #��Ӵ���ǿ������
        name = sgmfile.rstrip('.sgm')    
        chainstrength = pickle.load(open(csdir+name+'.p','rb')) #����α���ӷֽ����ǿ��
        gap_amount = len(chainstrength['oneword'])  
        cs_types = ('oneword','twoword','onesyl','twosyl')
        
        for d in train:#����isboundary����Ӵ���ǿ����
            boundary_index = d['zi_index']/w_cs - 1
            index_l = int(boundary_index)#��߷ֽ�����
            if boundary_index == int(boundary_index):   #stt�߽��α���ӱ߽��غ�
                s1,s2,s3,s4 = [chainstrength[t][index_l] for t in cs_types]
            else:
                left = (index_l+1)*w_cs    #��ߴʵ����
                if index_l >= gap_amount-1 or boundary_index < 0:  #�����/��ߵ�ͷ,ע��int(-0.3)=0
                    s1,s2,s3,s4 = [chainstrength[t][index_l] for t in cs_types]
                else:
                    index_r = ceil(boundary_index)
                    right = (index_r+1)*w_cs
                    strengthweight_l = d['zi_index']-left
                    strengthweight_r = right - d['zi_index']    #������α���ӷֽ�֮��,��Ȩƽ��
                    s1,s2,s3,s4 = [chainstrength[t][index_l]*strengthweight_r/w_cs + chainstrength[t][index_r]*strengthweight_l/w_cs for t in cs_types]
            d['oneword'],d['twoword'],d['onesyl'],d['twosyl'] = s1, s2, s3, s4 
        
        for t in cs_types:  #����ǿ��������һ��+��ɢ
            strength = np.array([d[t] for d in train],dtype=np.float)
            Fmax = max(strength)
            Fmin = min(strength)
            denominator = Fmax - Fmin
            strength = np.array([(s-Fmin)/denominator for s in strength])
            centers,_ = vq.kmeans(strength,initial4,iter=30)
            centers.sort()  #��code��С��������,����code�Ĵ�С��ʵ�ʴ�С���ܶ�Ӧ
            code,_ = vq.vq(strength,centers)
            for c,d in zip(code,train):
                d[t] = c  #��ɢ��
        
        def extend(l):    
            ex_l = deque(l) #����α���ӷֽ����ǿ��,deque���������exten
            ex_l.extendleft([0,0,0])   #�����߸��������-1
            ex_l.extend([0,0,0])
            return ex_l
        
        ow_list = extend([d['oneword'] for d in train])  #oneword_list
        os_list = extend([d['onesyl'] for d in train])   #onesyl_list
        tw_list = extend([d['twoword'] for d in train])  #twoword_list
        ts_list = extend([d['twosyl'] for d in train])   #twosyl_list
        
        for d in train: #�洢����ǿ�ȵ���������Ϣ
            index = train.index(d)
            d['ow'] = {}
            d['os'] = {}
            d['tw'] = {}
            d['ts'] = {}
            for t,l in zip(['ow','os','tw','ts'],[ow_list,os_list,tw_list,ts_list]):
                d[t]['0'] = l[index+3]
                d[t]['-3'],d[t]['-2'],d[t]['-1'] = [l[index],l[index+1],l[index+2]]
                d[t]['1'],d[t]['2'],d[t]['3'] = [l[index+4],l[index+5],l[index+6]]
                d[t] = OrderedDict(sorted(list(d[t].items()),key=lambda k:float(k[0])))

        '''
        #��ͼ��
        x = np.array(range(len(train)))
        y = np.array([d['oneword'] for d in train])
        y2 = np.array([d['onesyl'] for d in train])
        y3 = np.array([d['twoword'] for d in train])
        y4 = np.array([d['twosyl'] for d in train])
        y5 = np.array([d['isboundary'] for d in train])
        
        plt.plot(x,y,'red',label='oneword')
        #plt.plot(x,y2,'blue',label='onesyl')
        #plt.plot(x,y3,'green',label='twoword')
        #plt.plot(x,y4,'yellow',label='twosyl')
        plt.bar(x,y5*6,width=0.1)
        plt.legend()
        plt.show()
        '''
        
        #��Ӵʻ����ƶ�����,ע��:��Ȼ����similarity,��ʵ������depth_score,������Խ�͵÷�Խ��
        #��һ����(0,1)֮��
        name = sttfile.rstrip('.stt')    
        similarity = np.array(pickle.load(open(simdir+name+'.p','rb')),dtype=np.float)
        Fmax = max(similarity)
        Fmin = min(similarity)
        denominator = Fmax - Fmin
        similarity = np.array([(s-Fmin)/denominator for s in similarity])
        
        centers,_ = vq.kmeans(similarity,initial7,iter=30)
        centers.sort()  #��code��С��������,����code�Ĵ�С��ʵ�ʴ�С���ܶ�Ӧ
        code,_ = vq.vq(similarity,centers)
        similarity = [c for c in code]  #��ԭΪlist������Ӧcodeֵ����,ʵ����ɢ��
            
        similarity = deque(similarity) #����α���ӷֽ����ǿ��,deque���������extend
        similarity.extendleft([0,0,0])   #�����߸��������-1
        similarity.extend([0,0,0])
        for d in train:
            s_dict = {} #�洢similarity���ֵ�,key:-3,-2,-1,1,2,3
            boundary_index = d['zi_index']/w_s + 2
            index_l = int(boundary_index)
            if boundary_index == int(boundary_index):   #stt�߽��α���ӱ߽��غ�
                s_dict['-1'],s_dict['1'] = [similarity[index_l]] * 2
                s_dict['-2'],s_dict['-3'] = [similarity[index_l-1],similarity[index_l-2]]
                s_dict['2'],s_dict['3'] = [similarity[index_l+1],similarity[index_l+2]]
            else:
                index_r = index_l + 1
                s_dict['-1'],s_dict['1'] = [similarity[index_l],similarity[index_r]]
                s_dict['-2'],s_dict['-3'] = [similarity[index_l-1],similarity[index_r+1]]
                s_dict['2'],s_dict['3'] = [similarity[index_l-2],similarity[index_r+2]]
            #Ϊ����key���մ�-3��-1��˳������,����float(key)(ʵ����tuple[0])��������
            d['similarity'] = OrderedDict(sorted(list(s_dict.items()),key=lambda k:float(k[0])))
        
        
        ############################## ���˵���˱仯����,����res�ļ� #############################
        res_sph_lines = [l for l in res_lines if 'type=sph' in l]
        res_sph_tuples = []
        for line in res_sph_lines:
            obj = re.search(r'(?<=begt=)([^ ]+).*(?<=endt=)([^ ]+).*(?<=clusid=)([\d]+)',line)
            sph_seg = (obj.group(1), obj.group(2), obj.group(3))
            res_sph_tuples.append(sph_seg)
        res_non_lines = [l for l in res_lines if 'type=non' in l]
        
        res_non_tuples = [] #non���б�,����ɸѡtrain�е���(��ѡλ��)
        for line in res_non_lines:
            obj = re.search(r'(?<=begt=)([^ ]+).*(?<=endt=)([^ ]+)',line)
            non_seg = (obj.group(1), obj.group(2))
            res_non_tuples.append(non_seg)
            
        #��stt_timeline����ӵ�����:˵����id,�ñʼ��ϵķ�����res_sph_tuple��Ӧ
        def hms2s(res_time):
            #��res�е�ʱ��h:m:sת��Ϊ��s��ʾ,����֮��Ƚ�'''
            res_time_list = res_time.split(':')
            res = 0 #ת�����ʱ��
            if len(res_time_list) == 2:
                res = float(res_time_list[0])*60 + float(res_time_list[1])
            if len(res_time_list) == 3:
                res = float(res_time_list[0])*3600 + float(res_time_list[1])*60 \
                           + float(res_time_list[2])
            return res
        
        def calcoverlap(seg1,seg2):  #������������((h:m:s),(h:m:s))��ʽ��tuple,�����غ�ʱ�䳤��
            begt1, endt1 = [hms2s(seg1[0]),hms2s(seg1[1])]
            begt2, endt2 = [hms2s(seg2[0]),hms2s(seg2[1])]
            overlap = (endt1-begt1)+(endt2-begt2)-(max(endt1,endt2)-min(begt1,begt2))
            return overlap if overlap > 0 else 0
            
        for utt in stt_timeline:
            utt.append(res_sph_tuples[-1][2])
            maxoverlap = 0
            for res_sph in res_sph_tuples:
                overlap = calcoverlap(utt,(res_sph[0],res_sph[1]))
                if overlap > maxoverlap:
                    maxoverlap = overlap
                elif overlap < maxoverlap:
                    utt[2] = res_sph_tuples[res_sph_tuples.index(res_sph)-1][2]
                    break
        
        for d in train:#detect�ĸ�roi������˵���˱仯
            index = train.index(d)
            if stt_timeline[index][2] == stt_timeline[index+1][2]:
                d['spkchange'] = 0
            else:
                d['spkchange'] = 1
        
        for non in res_non_tuples:  #��.res�е�non�ζ�Ӧ��roi
            maxoverlap = 0
            for d in train:
                overlap = calcoverlap(non,(d['roi_begt'],d['roi_endt']))
                if overlap > maxoverlap:
                    maxoverlap = overlap
                elif overlap < maxoverlap:
                    index = train.index(d) - 1
                    d['isnon'] = 1
                    #print('non:'+str(non)+' '+'stt:'+train[index]['roi_begt']+' '+train[index]['roi_endt'])
                    break
        
        #���pitch����,�����������ڹ�һ��f0ƽ��ֵ,pitch reset
        tone_normalized = pickle.load(open(pitchdir+name+'_tone_nor.pitch','rb'))
        spk_normalized = pickle.load(open(pitchdir+name+'_spk_nor.pitch','rb'))
        #stt_roi��������pitch����ȡ����roi��,��Ϊ�����ж��stt_roi��Ӧ��һ��pitch_ri�����
        #���ǵ�ʱ��дtrainfileʱ�Ͱ�����stt_roi��pitch��һ�����������(��A),������Բ������Ǳ߽�
        #�����ĵĲ����Ǻܶ�
        for d in train:
            roi_begt = d['roi_begt']
            for roi in tone_normalized:
                if roi_begt == roi.stt_roi[0]:
                    index = tone_normalized.index(roi)
                    
                    array = np.array(roi.LEFT.f0_sequence,dtype=float)
                    left_avg_f0_tone_nor = array.mean()
                    d['laft'] = left_avg_f0_tone_nor
                    array = np.array(roi.RIGHT.f0_sequence,dtype=float)
                    right_avg_f0_tone_nor = array.mean()
                    d['raft'] = right_avg_f0_tone_nor
                    d['reset_t'] = d['raft'] - d['laft']
                    
                    array = np.array(spk_normalized[index].LEFT.f0_sequence,dtype=float)
                    left_avg_f0_spk_nor = array.mean()
                    d['lafs'] = left_avg_f0_spk_nor
                    array = np.array(spk_normalized[index].RIGHT.f0_sequence,dtype=float)
                    right_avg_f0_spk_nor = array.mean()
                    d['rafs'] = right_avg_f0_spk_nor
                    d['reset_s'] = d['rafs'] - d['lafs']
                    break
        
        
        #��������,��������������ת����(0,1)��Χ��,similarity֮ǰ�Ѿ���ɢ��,���ﲻ����
        features = ['lafs','rafs','laft','raft','reset_s','reset_t']
        for f in features:
            f_list = [d[f] for d in train if f in list(d.keys())]
            Fmax = max(f_list)
            Fmin = min(f_list)
            denominator = Fmax - Fmin
            for d in train:
                if f in list(d.keys()):
                    d[f] = (d[f]-Fmin)/denominator
            
        #k-means�㷨,�ֱ��ÿ���ļ���k-means
        #����features��������˳��,��ÿһ��������ͬ����������
        if kmeans:
            for f in features:
                f_list = [d[f] for d in train if f in list(d.keys())]
                f_list = np.array(f_list)
                centers,_ = vq.kmeans(f_list,initial5,iter=30)
                centers.sort()
                code,_ = vq.vq(f_list,centers)
                f_list = [c for c in code]
                index = 0
                for d in train:
                    if f in list(d.keys()):
                        d[f] = f_list[index]
                        index += 1
        
        boundary_deserted = open('boundary_deserted.txt','a+')  #�Ǳ߽絫�Ǵ�train�����ų�����
        
        def reserve(d): #�ж��Ƿ������roi hms2s(d['roi_endt']) - hms2s(d['roi_begt']) < 0.55  or  or 'lafs' not in list(d.keys())
            if hms2s(d['roi_endt']) - hms2s(d['roi_begt']) < 0.45:
                if d['isboundary']:
                    boundary_deserted.write(name + '\n')
                return 0
            else:
                return 1
            
        #train = [d for d in train if reserve(d)]    #ɸѡroi
            
        sgm.close()
        stt.close()
        res.close()
        pickle.dump(train,open('trainfile\\%s.train' % name,'wb'))
        print(name+' finished')        
    
    boundary_deserted.close()    

def kmeans_all():
    train_list = [pickle.load(open('trainfile\\%s' % f,'rb')) for f \
            in os.listdir('trainfile') if f.endswith('train')]
    name_list = [f.rstrip('.train') for f in os.listdir('trainfile') if f.endswith('train')]
    features = ['lafs','rafs','laft','raft','reset_s','reset_t']
    for f in features:
        f_list = []
        for train in train_list:
            temp = [d[f] for d in train if f in list(d.keys())]
            f_list.extend(temp)
        f_list = np.array(f_list)
        centers,_ = vq.kmeans(f_list,initial4,iter=30)
        centers.sort()
        code,_ = vq.vq(f_list,centers)
        f_list = [c for c in code]
        index = 0
        for train in train_list:
            for d in train:
                if f in list(d.keys()):
                    d[f] = f_list[index]
                    index += 1
    for train,name in zip(train_list,name_list):
        pickle.dump(train,open('trainfile\\%s.train' % name,'wb'))
    
    
if __name__ == '__main__':
    global initial2,initial3,initial4,initial5,initial6,initial7
    initial2 = np.array([0.25,0.75])
    initial3 = np.array([0.167,0.5,0.833])
    initial4 = np.array([0.125,0.375,0.625,0.875])
    initial5 = np.array([0.1,0.3,0.5,0.7,0.9])
    initial6 = np.array([0.083,0.25,0.417,0.583,0.75,0.917])
    initial7 = np.array([0.0714,0.214,0.357,0.5,0.643,0.786,0.926])
    main(nontrans='not include',kmeans=True)   #kmeans,�Ƿ��ÿ���ļ�����һ��,Falseʱ����kmeans_all
    #kmeans_all()