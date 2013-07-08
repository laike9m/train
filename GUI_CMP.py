#-*- coding:gbk -*-

from tkinter import *
from tkinter import font
import tkinter.ttk as ttk

class GUI_CMP():
    def __init__(self,name_list,ziseq_list,train_list,sgm_files):
        self.maindir = '..\wav_processing\output\\'
        self.ziseq_list = ziseq_list
        self.train_list = train_list
        self.name_list = name_list
        self.sgm_files = sgm_files
        self.tk = Tk()
        
        #右侧
        self.detect = ttk.Notebook(self.tk)
        self.detect.grid(row=0,column=1)
        self.pane1 = Frame(self.detect)
        self.pane2 = Frame(self.detect)
        self.detect.add(self.pane1,text='文字')
        self.detect.add(self.pane2,text='特征')
        #文字
        self.text_detect = Text(self.pane1,width=60,height=40)
        self.sb1 = Scrollbar(self.pane1,orient='vertical')
        self.text_detect.config(yscrollcommand=self.sb1.set)
        self.sb1.config(command=self.text_detect.yview)
        self.text_detect.grid(row=0,column=0)
        self.sb1.grid(row=0,column=1,sticky=NS)
        #特征
        self.f_detect = Text(self.pane2,width=60,height=40)
        self.sb2 = Scrollbar(self.pane2,orient='vertical')
        self.f_detect.config(yscrollcommand=self.sb2.set)
        self.sb2.config(command=self.f_detect.yview)
        self.f_detect.grid(row=0,column=0)
        self.sb2.grid(row=0,column=1,sticky=NS)
        
        #左侧
        self.F = Frame(self.tk)
        self.F.grid(row=0,column=0) 
        self.menu = Menubutton(self.F,text='选择文件')
        self.menu.grid(row=0,column=0,columnspan=2,sticky=W+E)
        self.menu.filelist = Menu(self.menu,tearoff=0)
        self.menu['menu']=self.menu.filelist
        
        self.text_sgm = Text(self.F,width=60,height=40)
        self.sb3 = Scrollbar(self.F,orient='vertical')
        self.text_sgm.config(yscrollcommand=self.sb3.set)
        self.sb3.config(command=self.text_sgm.yview)
        self.text_sgm.grid(row=1,column=0,sticky=NS)
        self.sb3.grid(row=1,column=1,sticky=NS)
        self.add_file_list()
        #self.show(self.name_list[0])
        self.tk.mainloop()
    
    def show(self,name):
        #显示文字
        #显示sgm
        index = self.name_list.index(name)
        data_sgm = open(self.maindir+self.sgm_files[index],'rt').read()
        #text_detect内容生成
        detect_text = self.ziseq_list[index][0]
        for d,seq in zip(self.train_list[index],self.ziseq_list[index][1:]):
            print(d['tag'])
            if d['tag']:
                detect_text += '\n\n'
                detect_text += seq
            else:
                detect_text += ' ' + seq
        #f_detect内容生成
        detect_f = self.ziseq_list[index][0]
        for d,seq in zip(self.train_list[index],self.ziseq_list[index][1:]):
            sim = str(d['similarity']).lstrip('OrderedDict')
            add = '\n%s//%s ow:%s os:%s sim:%s spk:%s' % (d['isboundary'],d['tag'],d['oneword']\
                                                    ,d['onesyl'],sim,d['spkchange'])
            add += '\n' + seq
            detect_f += add #如果想显示更多特征,在这里加入就行
                
        self.text_sgm.config(state=NORMAL)
        self.text_detect.config(state=NORMAL)
        self.f_detect.config(state=NORMAL)
        self.text_sgm.delete('1.0',END)
        self.text_detect.delete('1.0', END)
        self.f_detect.delete('1.0', END)
        
        self.text_sgm.insert('1.0', data_sgm)
        self.text_detect.insert('1.0', detect_text)
        self.f_detect.insert('1.0', detect_f)
        
        self.text_sgm.config(state=DISABLED)
        self.text_detect.config(state=DISABLED)
        self.f_detect.config(state=DISABLED)
        
        
    def add_file_list(self):
        #从文件列表中添加文件名到下拉菜单menubar
        for name in self.name_list:
            self.menu.filelist.add_command(label=name,command=lambda N=name:self.show(N))
    
    
if __name__ == '__main__':    
    gui_cmp = GUI_CMP(['a','b'],[],[])