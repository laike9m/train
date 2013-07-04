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
    '''若sgm大,返回正值；stt大返回负值.两个时间都是str类型'''
    stt_time_list = stt_time.split(':')
    stt = 0
    if len(stt_time_list) == 2:
        stt = float(stt_time_list[0])*60 + float(stt_time_list[1])
    if len(stt_time_list) == 3:
        stt = float(stt_time_list[0])*3600 + float(stt_time_list[1])*60 \
                   + float(stt_time_list[2])
    sgm = float(sgm_time)
    return sgm - stt    #返回float

def read_sgm(sgm_lines):
    '''
        从sgm文件中读取信息,具体来说
        最后一个有意义的段落是:
    <section type=report startTime=1560.100 endTime=1590.672>
        无意义的段落是:
    <section type=nontrans startTime=1590.672 endTime=1920.000>
        只要找到最后一个type是report的段落即可,该段的结束时间就是截断的时间
        这个函数在getpitch里也有,这里改造了一下
    '''
    section_lines = [l for l in sgm_lines if l.startswith('<section')]
    section_lines.reverse()
    for l in section_lines:
        if re.search('type=report',l):#最后一个有意义的段
            endt = re.search(r"(?<=endTime=)[\d.]*",l).group()
            return endt #返回最后一个有意义段落的结束时间
    


def main(nontrans,kmeans):
    '''入口函数'''
    maindir = '..\wav_processing\output\\'
    csdir = '..\LexicalChain\chainstrength\\'
    simdir = '..\Texttiling\similarity\\'
    pitchdir = '..\Pitch\output\\'
    sgmfiles = [f for f in os.listdir(maindir) if f.endswith('sgm')]
    sttfiles = [f for f in os.listdir(maindir) if f.endswith('stt')]
    resfiles = [f for f in os.listdir(maindir) if f.endswith('res')]
    w_cs = 40   #chainstrength 伪句子长度
    w_s = 20    #similarity 伪句子长度
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

        sgm_meaninful_end = read_sgm(sgm_lines)   #最后一个report段落的结束时间
        
        #形成stt的[[begt1,endt1],[begt2,endt2]]
        stt_timeline = []
        for line in stt_lines:
            obj = re.search(r'(?<=begt=)([^ ]+).*(?<=endt=)([^ ]+)',line)
            if obj:
                if time_cmp(sgm_meaninful_end, obj.group(1)) > 0:
                    t = [obj.group(1),obj.group(2)]
                    stt_timeline.append(t)
        
        #形成stt_roi_list:[(begt1,endt1),(begt2,endt2)],这已经是所有roi了
        stt_roi_list = []
        train = []
        for i in range(len(stt_timeline)-1):
            stt_roi_list.append((stt_timeline[i][1],stt_timeline[i+1][0]))
            d = {'roi_begt':stt_timeline[i][1],'roi_endt':stt_timeline[i+1][0], \
                 'isboundary':0,'isnon':0}
            d = OrderedDict(sorted(list(d.items())))
            train.append(d)
                
        sgm_timeline = []      #保存sgm段落起始/结束时间,跳过所有nontrans块  
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
            
                
        for t_sgm in sgm_timeline[1:]:  #把sgm boundary对应到stt_roi
            smallest = 1000000
            for t_stt in stt_roi_list:
                delta1 = abs(time_cmp(t_sgm[0],t_stt[0]))
                delta2 = abs(time_cmp(t_sgm[0],t_stt[1]))
                delta = delta1 if delta1<delta2 else delta2
                if smallest > delta:
                    smallest = delta
                else:
                    train[stt_roi_list.index(t_stt)-1]['isboundary'] = 1
                    break   #delta开始增大,说明上一个就是最近时间点,这个roi就是边界    
        
        seg_info = []   #构造seg_info,和get_chain里面seg_info是同样的东西
        stt_block_start = [d['roi_endt'] for d in train if d['isboundary']]
        stt_block_start.insert(0, stt_timeline[0][0])#插入第一个stt句子的起始时间
        ziseq_of_utt = []   #每个句子的字序列,['江泽民...','胡锦涛...',]
        for line in stt_lines:#构成seg_info
            match = re.search(r'(?<=zi=)[^ ]*',line)
            obj = re.search(r'(?<=begt=)([^ ]+).*(?<=endt=)([^ ]+)',line)
            if match and obj:
                ziseq_of_utt.append(match.group())
                begt = obj.group(1)
                if begt in stt_block_start:#是段落开始
                    new_segment = {}
                    new_segment['begt'] = begt
                    new_segment['zi'] = ''
                    new_segment['zi'] += match.group()
                    new_segment['length'] = len(new_segment['zi'])
                    seg_info.append(new_segment)
                else:
                    seg_info[-1]['zi'] += match.group()
                    seg_info[-1]['length'] = len(seg_info[-1]['zi'])
        
        zi_accumulate = []  #每句话结束字对应stt中的第几个字,累积
        for ziseq in ziseq_of_utt:
            if len(zi_accumulate) == 0:
                zi_accumulate.append(len(ziseq))
            else:
                zi_accumulate.append(zi_accumulate[-1]+len(ziseq))
            
        for d,zi_index in zip(train, zi_accumulate):#train添加zi_index项
            d['zi_index'] = zi_index
        
        
        #添加词链强度特征
        name = sgmfile.rstrip('.sgm')    
        chainstrength = pickle.load(open(csdir+name+'.p','rb')) #加载伪句子分界词链强度
        gap_amount = len(chainstrength['oneword'])  
        cs_types = ('oneword','twoword','onesyl','twosyl')
        
        for d in train:#对是isboundary处添加词链强度项
            boundary_index = d['zi_index']/w_cs - 1
            index_l = int(boundary_index)#左边分界的序号
            if boundary_index == int(boundary_index):   #stt边界和伪句子边界重合
                s1,s2,s3,s4 = [chainstrength[t][index_l] for t in cs_types]
            else:
                left = (index_l+1)*w_cs    #左边词的序号
                if index_l >= gap_amount-1 or boundary_index < 0:  #如果右/左边到头,注意int(-0.3)=0
                    s1,s2,s3,s4 = [chainstrength[t][index_l] for t in cs_types]
                else:
                    index_r = ceil(boundary_index)
                    right = (index_r+1)*w_cs
                    strengthweight_l = d['zi_index']-left
                    strengthweight_r = right - d['zi_index']    #在两个伪句子分界之间,加权平均
                    s1,s2,s3,s4 = [chainstrength[t][index_l]*strengthweight_r/w_cs + chainstrength[t][index_r]*strengthweight_l/w_cs for t in cs_types]
            d['oneword'],d['twoword'],d['onesyl'],d['twosyl'] = s1, s2, s3, s4 
        
        for t in cs_types:  #词链强度特征归一化+离散
            strength = np.array([d[t] for d in train],dtype=np.float)
            Fmax = max(strength)
            Fmin = min(strength)
            denominator = Fmax - Fmin
            strength = np.array([(s-Fmin)/denominator for s in strength])
            centers,_ = vq.kmeans(strength,initial4,iter=30)
            centers.sort()  #让code从小到大排列,这样code的大小和实际大小就能对应
            code,_ = vq.vq(strength,centers)
            for c,d in zip(code,train):
                d[t] = c  #离散化
        
        def extend(l):    
            ex_l = deque(l) #加载伪句子分界词链强度,deque可以在左边exten
            ex_l.extendleft([0,0,0])   #在两边各添加三项-1
            ex_l.extend([0,0,0])
            return ex_l
        
        ow_list = extend([d['oneword'] for d in train])  #oneword_list
        os_list = extend([d['onesyl'] for d in train])   #onesyl_list
        tw_list = extend([d['twoword'] for d in train])  #twoword_list
        ts_list = extend([d['twosyl'] for d in train])   #twosyl_list
        
        for d in train: #存储词链强度的上下文信息
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
        #画图用
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
        
        #添加词汇相似度特征,注意:虽然叫做similarity,但实际上是depth_score,相似性越低得分越高
        #归一化到(0,1)之间
        name = sttfile.rstrip('.stt')    
        similarity = np.array(pickle.load(open(simdir+name+'.p','rb')),dtype=np.float)
        Fmax = max(similarity)
        Fmin = min(similarity)
        denominator = Fmax - Fmin
        similarity = np.array([(s-Fmin)/denominator for s in similarity])
        
        centers,_ = vq.kmeans(similarity,initial7,iter=30)
        centers.sort()  #让code从小到大排列,这样code的大小和实际大小就能对应
        code,_ = vq.vq(similarity,centers)
        similarity = [c for c in code]  #还原为list并用相应code值代替,实现离散化
            
        similarity = deque(similarity) #加载伪句子分界词链强度,deque可以在左边extend
        similarity.extendleft([0,0,0])   #在两边各添加三项-1
        similarity.extend([0,0,0])
        for d in train:
            s_dict = {} #存储similarity的字典,key:-3,-2,-1,1,2,3
            boundary_index = d['zi_index']/w_s + 2
            index_l = int(boundary_index)
            if boundary_index == int(boundary_index):   #stt边界和伪句子边界重合
                s_dict['-1'],s_dict['1'] = [similarity[index_l]] * 2
                s_dict['-2'],s_dict['-3'] = [similarity[index_l-1],similarity[index_l-2]]
                s_dict['2'],s_dict['3'] = [similarity[index_l+1],similarity[index_l+2]]
            else:
                index_r = index_l + 1
                s_dict['-1'],s_dict['1'] = [similarity[index_l],similarity[index_r]]
                s_dict['-2'],s_dict['-3'] = [similarity[index_l-1],similarity[index_r+1]]
                s_dict['2'],s_dict['3'] = [similarity[index_l-2],similarity[index_r+2]]
            #为了让key按照从-3到-1的顺序排列,按照float(key)(实际是tuple[0])做了排序
            d['similarity'] = OrderedDict(sorted(list(s_dict.items()),key=lambda k:float(k[0])))
        
        
        ############################## 添加说话人变化特征,利用res文件 #############################
        res_sph_lines = [l for l in res_lines if 'type=sph' in l]
        res_sph_tuples = []
        for line in res_sph_lines:
            obj = re.search(r'(?<=begt=)([^ ]+).*(?<=endt=)([^ ]+).*(?<=clusid=)([\d]+)',line)
            sph_seg = (obj.group(1), obj.group(2), obj.group(3))
            res_sph_tuples.append(sph_seg)
        res_non_lines = [l for l in res_lines if 'type=non' in l]
        
        res_non_tuples = [] #non段列表,用来筛选train中的项(候选位置)
        for line in res_non_lines:
            obj = re.search(r'(?<=begt=)([^ ]+).*(?<=endt=)([^ ]+)',line)
            non_seg = (obj.group(1), obj.group(2))
            res_non_tuples.append(non_seg)
            
        #在stt_timeline中添加第三项:说话人id,用笔记上的方法和res_sph_tuple对应
        def hms2s(res_time):
            #把res中的时间h:m:s转化为以s表示,方便之后比较'''
            res_time_list = res_time.split(':')
            res = 0 #转换后的时间
            if len(res_time_list) == 2:
                res = float(res_time_list[0])*60 + float(res_time_list[1])
            if len(res_time_list) == 3:
                res = float(res_time_list[0])*3600 + float(res_time_list[1])*60 \
                           + float(res_time_list[2])
            return res
        
        def calcoverlap(seg1,seg2):  #输入两个按照((h:m:s),(h:m:s))形式的tuple,计算重合时间长度
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
        
        for d in train:#detect哪个roi左右有说话人变化
            index = train.index(d)
            if stt_timeline[index][2] == stt_timeline[index+1][2]:
                d['spkchange'] = 0
            else:
                d['spkchange'] = 1
        
        for non in res_non_tuples:  #将.res中的non段对应到roi
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
        
        #添加pitch特征,包含左右音节归一化f0平均值,pitch reset
        tone_normalized = pickle.load(open(pitchdir+name+'_tone_nor.pitch','rb'))
        spk_normalized = pickle.load(open(pitchdir+name+'_spk_nor.pitch','rb'))
        #stt_roi的数量比pitch里面取出的roi多,因为后者有多个stt_roi对应到一个pitch_ri的情况
        #于是到时候写trainfile时就把这种stt_roi的pitch给一个特殊的特征(如A),代表绝对不可能是边界
        #这样的的并不是很多
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
        
        
        #按照文献,将连续特征首先转化到(0,1)范围内,similarity之前已经离散化,这里不管了
        features = ['lafs','rafs','laft','raft','reset_s','reset_t']
        for f in features:
            f_list = [d[f] for d in train if f in list(d.keys())]
            Fmax = max(f_list)
            Fmin = min(f_list)
            denominator = Fmax - Fmin
            for d in train:
                if f in list(d.keys()):
                    d[f] = (d[f]-Fmin)/denominator
            
        #k-means算法,分别对每个文件作k-means
        #按照features中特征的顺序,给每一种特征不同的量化阶数
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
        
        boundary_deserted = open('boundary_deserted.txt','a+')  #是边界但是从train里面排除的项
        
        def reserve(d): #判断是否保留这个roi hms2s(d['roi_endt']) - hms2s(d['roi_begt']) < 0.55  or  or 'lafs' not in list(d.keys())
            if hms2s(d['roi_endt']) - hms2s(d['roi_begt']) < 0.45:
                if d['isboundary']:
                    boundary_deserted.write(name + '\n')
                return 0
            else:
                return 1
            
        #train = [d for d in train if reserve(d)]    #筛选roi
            
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
    main(nontrans='not include',kmeans=True)   #kmeans,是否对每个文件作归一化,False时调用kmeans_all
    #kmeans_all()