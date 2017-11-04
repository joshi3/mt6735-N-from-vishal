#!/usr/bin/env python
#encoding=utf-8
#author:wangfei
import commands
import sys
import os
import stat
import shutil
import subprocess
import tempfile
import sys
import types

class BoolCalculator():
    def __init__(self,expression):
        self.expression=expression.replace("&&","*").replace("||","+")
        self.suffix_list=[]
        self.dictopt={"+":2,"*":4,"!":7," ":0,"(":-1,")":8} #优先级
    def get_result(self):
        self.suffix_list=self.parse_expression(self.expression)
        tmp_list=[]
        #print "self.suffix_list:",self.suffix_list 
        for i in self.suffix_list:
            if not self.differ(i):
                tmp_list.append(i)
            else:
                right=tmp_list.pop()
                print "self.dictopt:",self.dictopt[i],i,tmp_list
                if self.dictopt[i]%2 == 0:
                    left=tmp_list.pop()
                else:
                    left=None 
                res=self.calc(i,str(right),str(left))
                tmp_list.append(res)
        return tmp_list[0]


    def get_sorted_expression(self,expression):
       listopt=[" "]
       listnum=[" "]

       for i in range(0,len(expression)):
           if(self.differ(expression[i])==1):
               if(len(listopt)):
                   if(self.dictopt[expression[i]] > self.dictopt[listopt[len(listopt)-1]]):
                      if expression[i]==")":
                         while(1):
                            tmp=listopt.pop()
                            if tmp=="(":
                               break
                            else:
                               listnum.append(" ")
                               listnum.append(tmp)
                               listnum.append(" ")
                      else:
                         listopt.append(expression[i])
                      
                   else:                     
                      if expression[i]=="(": 
                         listopt.append(expression[i])
                      else:
                         while(self.dictopt[expression[i]]<self.dictopt[listopt[len(listopt)-1]] and len(listopt)!=0):
                            tmp=listopt.pop()
                            listnum.append(tmp)
                            listnum.append(" ")
                         listopt.append(expression[i])
           else:                             
              listnum.append(expression[i])
       while(len(listopt)):                 
          listnum.append(" ")
          listnum.append(listopt.pop())
       return listnum

    def differ(self,elem):
        if elem=="+" or elem=="*" or elem=="!" or elem=="(" or elem==")":
            return 1
        else:
            return 0
    def parse_expression(self,expression):
       tmp_list=self.get_sorted_expression(expression)
       #print "tmp_list:",tmp_list
       last_string="".join(tmp_list)
       cnt_string=last_string.replace("  "," ")
       cnt_string=cnt_string[1:len(cnt_string)-1]
       cnt_list_tmp=cnt_string.split(" ")
       for i in cnt_list_tmp:
          if i!="":
             self.suffix_list.append(i)
       #print self.suffix_list
       return self.suffix_list

    def get_bool(self,value):
        #print "value:",value
        value=value.lower().strip()
        if value == "true" or value == "yes" or value == "y" or (value.isdigit() and int(value)!=0) or (not value.isdigit() and value != "no" and value != "n" and value != "false" and len(value)>0):
            return True
        return False
        
    def calc(self,operator,x,y=None):
        '''
        calculation  = {"+":lambda x,y:( eval(x) + eval(y)),
                        "*":lambda x,y:( eval(x) * eval(y)),
                        "!":lambda x,y:( eval(x) - eval(y)),
                        }
        '''
        if operator == '!':
            res = not self.get_bool(x)
        elif operator == '*':
            res =  self.get_bool(y) and self.get_bool(x)
        elif operator == '+':
            res = self.get_bool(y) or self.get_bool(x)
        else:
            print "not supported operator:",operator
            sys.exit(-1)
        print "operator %s,%s,%s,res:%s\n"%(operator,x,y,res)
        return res


#main
'''
if len(sys.argv) > 1:
    expression=sys.argv[1:]
    expression=" ".join(expression)
else:
    expression="no || n || no || no"
print expression
worker=BoolCalculator(expression)
answer=worker.get_result()
print answer
'''
