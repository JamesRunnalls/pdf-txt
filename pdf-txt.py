
# coding: utf-8

from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LTTextBoxHorizontal
from functools import reduce
import pandas as pd
import re
import os

def pdf_to_txt(pdf_name):
   
   # Variables
   
   sensitivity = 3 # Distance for lines to count as same line
   header = 750 # Cut off text above this height
   footer = 80 # Cutt off text below this height
   
   # Functions
   
   def order_pdf_textboxes(pdf_data,sensitivity,header,footer):
       df = pd.DataFrame(pdf_data)
       df.columns = ['x1','y1','x2','y2','Text']
       df['x1'] = pd.to_numeric(df.x1)
       df['x2'] = pd.to_numeric(df.x2)
       df['y1'] = pd.to_numeric(df.y1)
       df['y2'] = pd.to_numeric(df.y2)
       df = splitDataFrameList(df,'Text','\n')
       df = df.sort_values(['y2_new'],ascending=False).reset_index(drop=True)
       df.insert(0, 'Group', range(-1, -1 - len(df),-1))
       i = 0
       for index, row in df.iterrows():
           i = i + 1
           try:
               if abs(df.iloc[index]['y2_new'] - df.iloc[index+1]['y2_new']) < sensitivity:
                   df.set_value(index,'Group',i)
                   df.set_value(index+1,'Group',i)  
           except:
               pass
       df = df.sort_values(['x1'],ascending=True).reset_index(drop=True)
       df1 = df.groupby('Group', as_index=False).agg({'y2_new':'first','x1':'first'})
       df = df.groupby(['Group'])['Text'].apply(lambda x: ' '.join(x.astype(str))).reset_index()
       df['y2_new'] = df1['y2_new']
       df = df.sort_values(['y2_new'],ascending=False)
       df = df[df.y2_new > footer]
       df = df[df.y2_new < header]
       return df['Text'].tolist()

   def splitDataFrameList(df,target_column,separator):
       def splitListToRows(row,row_accumulator,target_column,separator):
           split_row = row[target_column].split(separator)
           del split_row[-1]
           i = 0
           for s in split_row:
               new_row = row.to_dict()
               new_row[target_column] = s
               line_height = (new_row['y2']-new_row['y1'])/(len(split_row))
               new_row['y2_new'] = new_row['y2'] - (i * line_height)
               new_row['y1_new'] = new_row['y2'] - ((i + 1) * line_height)
               i = i + 1
               row_accumulator.append(new_row)
       new_rows = []
       df.apply(splitListToRows,axis=1,args = (new_rows,target_column,separator))
       new_df = pd.DataFrame(new_rows)
       return new_df

   def extract_from_element(x):
       text = x.get_text()
       text = re.sub('"',"'",str(text))
       reps = ("\u201c",'"'),       ("\u201d",'"'),       ("\u2013",'-'),       ("\u2019","'"),       ("\uf06c",'-'),       ("\uf06c",'-'),       ("\u2122",'(TM)'),       ("\uf0b7",'-'),       ("\u01b7",'3'),       ("\u0e00",' '),       ("(cid:149)",'x')
       text = reduce(lambda a, kv: a.replace(*kv), reps, text)
       dims = str(x).split(' ')[1].split(',')
       return dims + [text]

   def list_to_txt(lists,fname):
       thefile = open(fname.replace(".pdf",".txt"), 'w')
       for item in lists:
           item = str(item.encode("utf-8"))
           item = item[2:-1]
           thefile.write("%s\n" % item)
           
   # PDF extract code 
   
   document = open(pdf_name, 'rb')
   #Create resource manager
   rsrcmgr = PDFResourceManager()
   # Set parameters for analysis.
   laparams = LAParams()
   # Create a PDF page aggregator object.
   device = PDFPageAggregator(rsrcmgr, laparams=laparams)
   interpreter = PDFPageInterpreter(rsrcmgr, device)
   pdf_full = []
   #Loop through the pages
   for page in PDFPage.get_pages(document):
       pdf_data = []
       interpreter.process_page(page)
       # receive the LTPage object for the page.
       layout = device.get_result()
       # Extract only the text objects
       for element in layout:
           if "LTTextBoxHorizontal" not in str(element): 
               continue
           else:
               pdf_data.append(extract_from_element(element)) 
       pdf_full = pdf_full + order_pdf_textboxes(pdf_data,sensitivity,header,footer)
       
   list_to_txt(pdf_full,pdf_name)
