import streamlit as st 
import numpy as np 
import docx
import os
import pandas as pd
import openpyxl
import shutil
from copy import copy
from openpyxl.styles import Font, Border, PatternFill, Protection, Alignment
import datetime
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
import base64
import streamlit.components.v1 as components

# 设置网页标题，以及使用宽屏模式
st.set_page_config(
    page_title="TAXI_TIME",
    layout="wide"

)
# 隐藏右边的菜单以及页脚
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
def download_button(file_path, button_text):
    with open(os.path.abspath(file_path), 'rb') as f:
        bytes = f.read()
        b64 = base64.b64encode(bytes).decode()

    # 创建一个名为 "Download File" 的下载链接
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">{button_text}</a>'

    # 在 Streamlit 应用程序中使用按钮链接
    st.markdown(f'<div class="button-container">{href}</div>', unsafe_allow_html=True)

    # 添加 CSS 样式以将链接样式化为按钮
    st.markdown("""
        <style>
        .button-container {
            display: inline-block;
            margin-top: 1em;
        }
        .button-container a {
            background-color: #0072C6;
            border: none;
            color: white;
            padding: 0.5em 1em;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            font-weight: bold;
            border-radius: 4px;
            cursor: pointer;
        }
        .button-container a:hover {
            background-color: #005AA3;
        }
        </style>
    """, unsafe_allow_html=True)

class ana2:
    def __init__(self,source_file1,st):        
        self.source_file1 = source_file1
        self.st=st
        self.key=0
    def reading(self):
        df=pd.read_excel(self.source_file1)
        # 去除逗号
        df['计划落地剩油'] = df['计划落地剩油'].str.replace(',', '')
        df['实际落地剩油'] = df['实际落地剩油'].str.replace(',', '')
        # 将列转换为数字类型
        df['计划落地剩油'] = df['计划落地剩油'].astype(float)
        df['实际落地剩油'] = df['实际落地剩油'].astype(float)
        df['实际落地剩油可飞行时间'] = df['实际落地剩油可飞行时间'].astype(float)
        # 按照签派员姓名和机型对DataFrame进行分组，并计算平均值
        if '机型' in df.columns:
            grouped_df = df.groupby(['签派员姓名', '机型']).agg({'实际落地剩油': 'mean', '实际落地剩油可飞行时间': 'mean'})
            self.key=1
        else:
            grouped_df = df.groupby(['签派员姓名']).agg({'实际落地剩油平均值': 'mean', '实际落地剩油可飞行时间平均值': 'mean'})
        grouped_df = grouped_df.rename(columns={'实际落地剩油': '实际落地剩油平均值', '实际落地剩油可飞行时间': '实际落地剩油可飞行时间平均值'})
        # 重置索引
        grouped_df = grouped_df.reset_index()

        # 显示新的DataFrame
        return grouped_df
    def report(self):
        df=self.reading()
        if self.key==1:
            report_df=df.groupby(['签派员姓名']).agg({'实际落地剩油平均值': 'mean', '实际落地剩油可飞行时间平均值': 'mean'})
        else:
            report_df=df
        return report_df
st.write("## 平均落地剩油")
st.markdown('<span style="color:red;">请注意上传文件需要有（签派员姓名/实际落地剩油/实际落地剩油可飞行时间）</span>', unsafe_allow_html=True)
source_file1 = st.file_uploader("上传文件：")
if source_file1 is not None:
    anay=ana2(source_file1,st)
    grouped_df=anay.reading()
    report_df=anay.report()
    jud=anay.key
    if jud==1:
        checked = st.checkbox("是否按照机型细分")
        if checked:
            st.write(grouped_df)
        else:
            st.write(report_df)
    else:
        st.write(report_df)
        
    with st.form(key='my_form'):
        st.write('筛选条件')
        # 获取唯一的签派员姓名
        unique_names = grouped_df['签派员姓名'].unique()
        # 创建下拉菜单
        selected_name = st.selectbox("选择签派员姓名", options=unique_names)
        filtered_df = grouped_df[grouped_df['签派员姓名'] == selected_name]
        # 提交按钮
        submit_button = st.form_submit_button(label='提交')
    if submit_button:
        st.write(filtered_df)
        
else:
    st.warning('未上传文件')



