# -*- coding:gbk -*-

import pickle
import os
import GUI_CMP
from copy import deepcopy

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

def all_f():
    #生成包含全部特征的训练文件,先对每个文件分别生成,然后合并
    for train,name in zip(train_list,name_list):
        crfsuite = open('trainfile\\%s.train.crfsuite' % name, 'wt')
        for d in train:
            values_part1 = (d['isboundary'],d['cs_oneword'],d['cs_twoword'],d['cs_onesyl'],d['cs_twosyl'],
                        d['similarity']['-3'],d['similarity']['-2'],d['similarity']['-1'],
                        d['similarity']['1'],d['similarity']['2'],d['similarity']['3'],
                        d['similarity']['-2'],d['similarity']['-1'],
                        d['similarity']['-3'],d['similarity']['-2'],d['similarity']['-1'],
                        d['similarity']['1'],d['similarity']['2'],
                        d['similarity']['1'],d['similarity']['2'],d['similarity']['3'],
                        d['spkchange'])
            if 'lafs' in list(d.keys()):
                values_part2 = (d['laft'],d['raft'],d['reset_t'],d['lafs'],d['rafs'],d['reset_s'])
            else:
                values_part2 = ('A','A','A','A','A','A')
            values = values_part1 + values_part2
            values = tuple([str(v) for v in values])
            line = '%s\tcs_oneword=%s\tcs_twoword=%s\tcs_onesyl=%s\tcs_twosyl=%s\t\
            s[-3]=%s\ts[-2]=%s\ts[-1]=%s\ts[1]=%s\ts[2]=%s\ts[3]=%s\ts[-2]|s[-1]=%s|%s\t\
            s[-3]|s[-2]|s[-1]=%s|%s|%s\ts[1]|s[2]=%s|%s\ts[1]|s[2]|s[3]=%s|%s|%s\tspk=%s\t\
            laft=%s\traft=%s\treset_t=%s\tlafs=%s\trafs=%s\treset_s=%s' % values
            crfsuite.write(line + '\n')
        crfsuite.close()
    Merge('all')
    
def one_f():
    #生成仅包含某一种特征的训练文件
    for train,name in zip(train_list,name_list):
        crfsuite = open('trainfile\\%s.train.crfsuite' % name, 'wt')
        for d in train:
            values = (d['isboundary'],d['spkchange'])
            line = '%s\tcs_oneword=%s' % values
            crfsuite.write(line + '\n')
        crfsuite.close()
    Merge('one')

def add_chain(line,d):  #添加词链特征
    return line+'\tow[-3]=%s\tow[-2]=%s\tow[-1]=%s\tow[0]=%s\tow[1]=%s\tow[2]=%s\tow[3]=%s\t\
            ow[-3]|ow[-2]|ow[-1]|ow[0]=%s|%s|%s|%s\t\
            os[-2]|os[-1]|os[0]=%s|%s|%s\t\
            ow[0]|ow[1]|ow[2]|ow[3]=%s|%s|%s|%s\
            os[0]|os[1]|os[2]=%s|%s|%s\
            \tos[-3]=%s\tos[-2]=%s\tos[-1]=%s\tos[0]=%s\tos[1]=%s\tos[2]=%s\tos[3]=%s\t\
            os[-3]|os[-2]|os[-1]|os[0]=%s|%s|%s|%s\t\
            os[0]|os[1]|os[2]|os[3]=%s|%s|%s|%s' % \
        (d['ow']['-3'],d['ow']['-2'],d['ow']['-1'],d['ow']['0'],d['ow']['1'],d['ow']['2'],d['ow']['3'],
         d['ow']['-3'],d['ow']['-2'],d['ow']['-1'],d['ow']['0'],
         d['ow']['-3'],d['ow']['-2'],d['ow']['-1'],
         d['ow']['0'],d['ow']['1'],d['ow']['2'],d['ow']['3'],
         d['ow']['1'],d['ow']['2'],d['ow']['3'],
         d['os']['-3'],d['os']['-2'],d['os']['-1'],d['os']['0'],d['os']['1'],d['os']['2'],d['os']['3'],
         d['os']['-3'],d['os']['-2'],d['os']['-1'],d['os']['0'],
         d['os']['0'],d['os']['1'],d['os']['2'],d['os']['3'],
         )

          
def add_sim(line,d):    #添加相似度特征
    return line+'\ts[-3]=%s\ts[-2]=%s\ts[-1]=%s\ts[1]=%s\ts[2]=%s\ts[3]=%s\ts[-2]|s[-1]=%s|%s\t\
            s[-3]|s[-2]|s[-1]=%s|%s|%s\ts[1]|s[2]=%s|%s\ts[1]|s[2]|s[3]=%s|%s|%s' % \
            (d['similarity']['-3'],d['similarity']['-2'],d['similarity']['-1'],
            d['similarity']['1'],d['similarity']['2'],d['similarity']['3'],
            d['similarity']['-2'],d['similarity']['-1'],
            d['similarity']['-3'],d['similarity']['-2'],d['similarity']['-1'],
            d['similarity']['1'],d['similarity']['2'],
            d['similarity']['1'],d['similarity']['2'],d['similarity']['3'])

    
def add_pitch(line,d):  #添加pitch特征
    if 'lafs' in list(d.keys()):
        values = (d['laft'],d['raft'],d['reset_t'],d['lafs'],d['rafs'],d['reset_s'])
    else:
        values = ('A','A','A','A','A','A')
    return line+'\tlaft=%s\traft=%s\treset_t=%s\tlafs=%s\trafs=%s\treset_s=%s' % values

def add_spk(line,d):    #添加说话人变化特征
    return line+'\tspk=%s' % d['spkchange']

def add_features(chain,sim,pitch,spk):  #选择特征
    for train,name in zip(train_list,name_list):
        crfsuite = open('trainfile\\%s.train.crfsuite' % name, 'wt')
        for d in train:
            line = '%s' % d['isboundary']
            if chain:
                line = add_chain(line,d)
            if sim:
                line = add_sim(line,d)
            if pitch:
                line = add_pitch(line,d)
            if spk:
                line = add_spk(line,d)
            crfsuite.write(line + '\n')
        crfsuite.close()
    Merge('select')
    os.system('select.bat')     #将结果显示在控制台
    os.system('select_tag.bat') #把tag的结果输出到文件

def fifteen():  #将原始结果按照15s原则重新计算准确召回f-measure
    tag_list = open('..\\..\\CRF_train\\tag_select.txt','r') #原始tag文件
    test_d_list = []    #把测试集中所有的dict放进一个列表
    for train in train_list[testslice]:
        for d in train:
            test_d_list.append(d)
    real_boundary = len([1 for d in test_d_list if d['isboundary']])
    tag_boundary = 0    #标记出的边界数量

    for d,tag in zip(test_d_list,tag_list):
        tag_boundary += int(tag)
        d['tag'] = int(tag) #在dict中添加tag用来表示是否被识别为边界,改变了原始的train因为test_d_list的元素是引用
    
    global test_list_cp
    test_list_cp = deepcopy(train_list[testslice])
    
    recall = 0  #正确识别的边界数量
    index = -1
    for d in test_d_list:
        index += 1
        if d['isboundary']:
            if d['tag']:  #tag=1,recall直接+1
                recall += 1
                d['tag'] = 0
                continue
            else:   #tag不是1,考察是否在+/-15s内有tag=1,且这个tag不能的位置isboundary不能为1
                left_distance = 100
                right_distance = 100
                for dleft in test_d_list[index::-1]:
                    if dleft['tag']:
                        left_distance = abs(hms2s(dleft['roi_endt'])-hms2s(d['roi_begt']))
                        break
                    else:
                        continue
                for dright in test_d_list[index:]:
                    if dright['tag']:
                        right_distance = abs(hms2s(dright['roi_begt'])-hms2s(d['roi_endt']))
                        break
                    else:
                        continue
                if (left_distance<15 and not dleft['isboundary']) or (right_distance<15 and not dright['isboundary']):
                    if left_distance < 15:
                        dleft['tag'] = 0    #使每个tag=1只能算一次,取左边的
                    else:
                        dright['tag'] = 0
                    recall += 1
        else:
            continue
    
    precision = recall/tag_boundary
    recall = recall/real_boundary
    f = 2*recall*precision/(recall + precision)
    print('pre:',precision,',recall:',recall,',f-measure:',f)

def Merge(ftype):
    #把训练文件合并起来,type用来标记合并文件中特征的种类,不同种类训练文件名字不同
    merged_trainfile = open('%s.train.crfsuite' % ftype,'wt')
    crfsuite_list = [f for f in os.listdir('trainfile') if f.endswith('.crfsuite')]
    for f in crfsuite_list[trainslice]:
        single_trainfile = open('trainfile\\%s' % f,'rt')
        data = single_trainfile.read()
        merged_trainfile.write(data)
        single_trainfile.close()
    merged_trainfile.close()
    testfile = open('%s.test.crfsuite' % ftype,'wt')
    for f in crfsuite_list[testslice]:
        single_trainfile = open('trainfile\\%s' % f,'rt')
        data = single_trainfile.read()
        testfile.write(data)
        single_trainfile.close()
    print(ftype + ' finished')
    testfile.close()
    os.system('move /y %s.train.crfsuite ..\\..\\CRF_train\\%s.train.crfsuite' % (ftype,ftype))
    os.system('move /y %s.test.crfsuite ..\\..\\CRF_train\\%s.test.crfsuite' % (ftype,ftype))

def main(mode='train'):
    '''
        两种模式,默认是train,先生成模型再测试,如果mode='test',表示用现有的模型做测试
        如果没有特殊情况就不再执行make_feature_dict,只运行这个文件
     mc一共有25个文件,用前20个训练，后5个测试
        根据调用的函数不同,生成的训练文件种类不同
        每个mc自己的训练文件是每次都覆盖,但是合并后的训练文件不会覆盖,除非运行生成同样特征训练文件的程序
    '''
    if mode == 'train':
        global train_list 
        train_list = [pickle.load(open('trainfile\\%s' % f,'rb')) for f \
                    in os.listdir('trainfile') if f.endswith('train')]
        global name_list
        name_list = [f.rstrip('.train') for f in os.listdir('trainfile') if f.endswith('train')]
        global trainslice,testslice
        trainslice = slice(0,20)
        testslice = slice(20,25)
        add_features(chain=1,sim=1,pitch=0,spk=1)
        fifteen()
    elif mode == 'test':
        pass
    else:
        print('模式选择错误,请检查参数')
    
    ziseq_list = [pickle.load(open('ziseq\\%s' % f,'rb')) for f \
                    in os.listdir('ziseq') if f.endswith('ziseq')]
    sgm_files = pickle.load(open('sgmfiles.p','rb'))
    gui = GUI_CMP.GUI_CMP(name_list[testslice],ziseq_list[testslice],test_list_cp,sgm_files[testslice])#显示图形界面  
        
        
    
if __name__ == '__main__':
    main()