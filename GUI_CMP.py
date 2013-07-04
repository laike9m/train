#-*- coding:gbk -*-

from tkinter import *
from tkinter import font
import tkinter.ttk as ttk

class GUI_CMP():
    def __init__(self):
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
        self.text_detect.config(yscrollcommand=self.sb1.set,state='disabled')
        self.sb1.config(command=self.text_detect.yview)
        self.text_detect.grid(row=0,column=0)
        self.sb1.grid(row=0,column=1,sticky=NS)
        #特征
        self.f_detect = Text(self.pane2,width=60,height=40)
        self.sb2 = Scrollbar(self.pane2,orient='vertical')
        self.f_detect.config(yscrollcommand=self.sb2.set,state='disabled')
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
        self.add_file_list()
        
        self.text_sgm = Text(self.F,width=60,height=40)
        self.sb3 = Scrollbar(self.F,orient='vertical')
        self.text_sgm.config(yscrollcommand=self.sb3.set,state='disabled')
        self.sb3.config(command=self.text_sgm.yview)
        self.text_sgm.grid(row=1,column=0,sticky=NS)
        self.sb3.grid(row=1,column=1,sticky=NS)
        
        self.tk.mainloop()
        
    def add_file_list(self):
        #从文件列表中添加文件名到下拉菜单menubar
        def k():
            pass
        self.menu.filelist.add_command(label='test',command=k,columnbreak=1)
        self.menu.filelist.add_command(label='test',command=k,columnbreak=1)
        self.menu.filelist.add_command(label='test',command=k,columnbreak=1)
        self.menu.filelist.add_command(label='test',command=k,columnbreak=1)
        self.menu.filelist.add_command(label='test',command=k,columnbreak=1)
        self.menu.filelist.add_command(label='test',command=k,columnbreak=1)
        self.menu.filelist.add_command(label='test',command=k,columnbreak=1)
        self.menu.filelist.add_command(label='test',command=k,columnbreak=1)
        self.menu.filelist.add_command(label='test',command=k,columnbreak=1)
        self.menu.filelist.add_command(label='test',command=k,columnbreak=1)
        pass
    
if __name__ == '__main__':
    gui_cmp = GUI_CMP()