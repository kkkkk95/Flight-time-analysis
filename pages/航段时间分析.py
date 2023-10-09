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

class ana:
    def __init__(self,source_file1,source_file2,st,taxitime):        
        self.source_file1 = source_file1
        self.source_file2 = source_file2
        #所需文件地址
        self.data0_abs_path=os.path.abspath(r'data/代码.xls')
        self.data1_abs_path = os.path.abspath(r'data/W23-001 UTC时.xlsx')
        self.data2_abs_path = os.path.abspath(r'data/平均飞行时间冬春.xls')
        self.data3_abs_path = os.path.abspath(r'data/2019民航国内航班标准航段运行时间表.xlsx')
        #设置的滑行时间
        self.taxitime=taxitime
        self.st=st
        self.switch_dic=self.switch_data()
    #时差转换
    def calculate_time_difference(self,timezone_str):
        sign = timezone_str[0]  # 提取符号
        hours = int(timezone_str[1:3])  # 提取小时部分
        minutes = int(timezone_str[4:6]) if len(timezone_str) >= 6 else 0  # 提取分钟部分（如果有的话）

        # 根据符号设置正负号
        if sign == 'E':
            sign = 1
        else:
            sign = -1

        # 计算时差
        time_zone_delta = timedelta(hours=sign * hours, minutes=sign * minutes)

        # 计算与北京时间的时差
        beijing_time_zone = timedelta(hours=8)  # 北京时间为东八区
        time_difference = time_zone_delta - beijing_time_zone

        return time_difference
    #三四字码和时差的字典
    def switch_data(self):
        switch_dic={}
        data0 = pd.read_excel(self.data0_abs_path)
        # 保留指定列
        data0 = data0.loc[:, ['icao_c3', 'icao_c4', 't_zone', 'c_name']]
        # 应用calculate_time_difference函数创建新列
        data0['time_difference'] = data0['t_zone'].apply(self.calculate_time_difference)
        switch_dic = data0.set_index('icao_c3')['icao_c4'].to_dict()
        return switch_dic
    #局方标准航段时间
    def standard_df(self):
        data3_abs_path = os.path.abspath(self.data3_abs_path)
        df=pd.read_excel(data3_abs_path,skiprows=1)
        # 处理合并单元格
        for col in df.columns:
            prev_value = None
            for i, cell in enumerate(df[col]):
                if pd.isna(cell):
                    if prev_value is not None:
                        df[col].iloc[i] = prev_value
                else:
                    prev_value = cell
        # 移除包含合并单元格的行
        df = df.dropna()
        # 重置索引
        df = df.reset_index(drop=True)
        # 提取四位大写字母
        pattern = r'([A-Z]{4})<->([A-Z]{4})'
        df[['起始点', '结束点']] = df['航段代号'].str.extract(pattern)

        # 使用字典进行转换
        # 创建反向字典
        reverse_dic = {value: key for key, value in self.switch_dic.items()}
        df['起始点'] = df['起始点'].replace(reverse_dic)
        df['结束点'] = df['结束点'].replace(reverse_dic)

        # 构建航段
        df['航段'] = df['起始点'] + '-' + df['结束点']
        #保留指定列
        df = df.loc[:, ['航段中文', '航段代号', '航段', '航季', '机型8(M0.8～0.89)', '机型7(M0.7～0.79)', '机型6(M0.6～0.69)', '机型5(M0.5～0.59)','机型4(M0.4～0.49)']]
        return df
    def std_sta(self):
        if self.source_file1 is None:
            data1 = pd.read_excel(self.data1_abs_path)
        else:
            data1 = pd.read_excel(self.source_file1)
        data1['航段'] = data1['Dept Arp'] + '-' + data1['Arvl Arp']
        # 将字符串类型的时间列转换为时间类型
        data1['Dept Time'] = pd.to_datetime(data1['Dept Time'], format='%H:%M:%S')
        data1['Arrv Time'] = pd.to_datetime(data1['Arrv Time'], format='%H:%M:%S')
        # 计算时间差，并转换为分钟的整数类型
        data1['航段时间'] = (data1['Arrv Time'] - data1['Dept Time']).dt.total_seconds() // 60
        # 处理跨天情况
        next_day_mask = data1['Arrv Time'] < data1['Dept Time']
        next_day_offset = timedelta(days=1)
        data1.loc[next_day_mask, '航段时间'] += next_day_offset.total_seconds() // 60
        return data1
    def avgtime(self):
        if self.source_file2 is None:
            data2 = pd.read_excel(self.data2_abs_path)
        else:
            data2 = pd.read_excel(self.source_file2)
        return data2
    def main(self):
        data1=self.std_sta()
        data2=self.avgtime()
        data=pd.merge(data1,data2,on='航段',how='outer')
        data = data.dropna(subset=['Flt Desg'])
        data['差值']=data['航段时间']-data['平均空中时间']+self.taxitime
        # 保留指定列
        data = data.loc[:, ['Flt Desg', 'Freq', 'Subfleet', 'Arvl Arp', '航段', '航段时间', '平均空中时间', '差值']]

        # 修改列名
        data = data.rename(columns={'Unnamed: 7': '目的地机场'})
        return data

st.write("## 修改滑行时间和数据表（如无需直接点击提交）")
with st.form(key='my_form'):
    # 用户输入滑行时间
    taxitime = st.number_input("输入滑行时间（分钟）", min_value=0, step=1, value=0)
    source_file1=source_file2=None
    col1, col2 = st.columns(2)
    with col1:
        source_file1 = st.file_uploader("上传文件(如需修改航段时间)：")
    with col2:
        source_file2 = st.file_uploader("上传文件(如需修改平均空中时间)：")
        
    # 提交按钮
    submit_button = st.form_submit_button(label='提交')

# 检查提交事件是否触发
if submit_button:
    anay=ana(source_file1,source_file2,st,taxitime)
    data=anay.main()
    standard_df=anay.standard_df()
    st.session_state.data=data
    st.session_state.stardard=standard_df

if not st.session_state.data.empty:
    data=st.session_state.data
    col1, col2 = st.columns(2)
    with col1:
        st.write("## 航段时间过长或过短数量及占比")
        # 筛选差值在不同范围内的数量
        range_counts = {
            '~-10': len(data[data['差值'] < -10]),
            '-10~0': len(data[(data['差值'] >= -10) & (data['差值'] < 0)]),
            '0~10': len(data[(data['差值'] >= 0) & (data['差值'] < 10)]),
            '40~50': len(data[(data['差值'] >= 40) & (data['差值'] < 50)]),
            '50~60': len(data[(data['差值'] >= 50) & (data['差值'] < 60)]),
            '60~': len(data[data['差值'] >= 60])
        }
        # 创建DataFrame
        df = pd.DataFrame.from_dict(range_counts, orient='index', columns=['数量'])
        df['占比'] = df['数量'] / len(data) * 100

        # 显示DataFrame
        st.dataframe(df)
        result=df.to_excel(os.path.abspath(r'result.xlsx'))
        download_button(os.path.abspath(r'result.xlsx'), 'download')
    with col2:
        st.write("## 柱状图展示")
        mpl.font_manager.fontManager.addfont('字体/SimHei.ttf') #临时注册新的全局字体
        plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
        plt.rcParams['axes.unicode_minus']=False#用来正常显示负号
        # 设置图形大小
        plt.figure(figsize=(5, 4))

        # 切片选择左侧和右侧数据
        short_df = df[:3]
        long_df = df[3:]

        # 绘制蓝色柱子
        plt.bar(short_df.index, short_df['占比'], color='blue')

        # 绘制红色柱子
        plt.bar(long_df.index, long_df['占比'], color='red')

        # 添加标注
        for i, value in enumerate(short_df['数量']):
            plt.text(i, short_df['占比'][i], f"{value}\n{short_df['占比'][i]:.2f}%", ha='center', va='bottom', color='blue')

        for i, value in enumerate(long_df['数量']):
            plt.text(i+3, long_df['占比'][i], f"{value}\n{long_df['占比'][i]:.2f}%", ha='center', va='bottom', color='red')
        # 添加标注说明
        plt.legend(handles=[plt.bar(0, 0, color='blue', label='过短'), plt.bar(0, 0, color='red', label='过长')], loc='upper left')

        # 设置标题和轴标签
        plt.title("过长过短航班数量及占比")
        plt.xlabel("范围")
        plt.ylabel("百分比%")

        # 显示图形
        st.pyplot(plt)
else:
    st.warning('请提交表单1')

st.write("## 筛选数据表（可按照‘航段时间-平均空中时间’或‘航段’筛选）")
col1, col2 = st.columns(2)
with col1:
    with st.form(key='my_form2'):
        min=st.number_input("航段时间-平均空中时间（最小值）", value=-10)
        max=st.number_input("航段时间-平均空中时间（最大值）", value=60)
        # 提交按钮
        submit_button2 = st.form_submit_button(label='提交')
    
with col2:
    with st.form(key='my_form3'):
        hangduan = st.text_input("航段查询", value='PEK-LAX')
        # 提交按钮
        submit_button3 = st.form_submit_button(label='提交')
st.write('---------')
st.write('筛选数据如下：')
result1,result2=st.columns(2)
if submit_button2 and not st.session_state.data.empty:
    df=data[(data['差值'] >= min) & (data['差值'] < max)]
    st.session_state.choosedata=df
elif submit_button3 and not st.session_state.data.empty:
    df=data[(data['航段'] == hangduan)]
    st.session_state.choosedata=df
elif st.session_state.choosedata.empty:
    st.warning('未选择筛选条件')
else:
    pass


with result1:
    if not st.session_state.choosedata.empty:
        st.write(st.session_state.choosedata)
        result=st.session_state.choosedata.to_excel(os.path.abspath(r'result.xlsx'))
        download_button(os.path.abspath(r'result.xlsx'), 'download')
        # 创建新的DataFrame用于存储航段和航班总数
        new_df = pd.DataFrame(columns=['航段', '航班总数'])
        df=st.session_state.choosedata
        if st.button('每周受影响航班量分析'):
            # 遍历每个航段，计算航班总数并添加到新的DataFrame中
            for segment in df['航段'].unique():
                total_flights = 0
                for index, row in df.iterrows():
                    if row['航段'] == segment:
                        freq_str = str(row['Freq'])
                        total_flights += len(freq_str)
                new_df = pd.concat([new_df, pd.DataFrame({'航段': [segment], '航班总数': [total_flights]})])

            # 按照航班总数从大到小排序新的DataFrame
            new_df = new_df.sort_values(by='航班总数', ascending=False)
            st.session_state.anadf=new_df 
        if not st.session_state.anadf.empty:
            st.write(st.session_state.anadf)

with result2:
    stardard = st.text_input("国内航班标准航段运行时间查询", value='PEK-XIY')
    if not st.session_state.stardard.empty:
        standard_df=st.session_state.stardard
        df=standard_df[standard_df['航段']==stardard]
        st.write(df)
    if st.button('查看说明和对应机型'):
        text = '''1、航段运行时间基础库中所有数值均为四位数，前两位表示小时数，后两位表示分钟数。如0150，表示对应航段的运行时间为1小时50分钟。
        2、部分城市对只有单向运行的时间，待有实际航班运行数据后将及时更新。
        3、该标准实施后，若城市对不在该表内，将先由航空公司提供估算的运行时间数据，待统计分析一段时间的运行数据后，再适时加入该标准内。'''

        st.markdown(text)
    options=['机型8(M0.8～0.89)','机型7(M0.7～0.79)','机型6(M0.6～0.69)','机型5(M0.5～0.59)','机型4(M0.4～0.49)']
    # 在应用程序中添加下拉菜单
    selected_option = st.selectbox('选择机型', options)
    type_dic={
        '机型8(M0.8～0.89)':'B767-200 B767-300 B767F B767 B747-200 B747-300 B747-400 B747F B747-8 B747 B777-200 B777-300 B777 A340-200 A340-300 A340-600 A340 A330-200 A330-300 A330 A350 MD11F MD11 DC10F DC10 A380 B787-8 B787-9 B787',
        '机型7(M0.7～0.79)':'A318 A319 A320 A321 A300-600 A300F A300 B737-200 B737-300 B737-400 B737-500 B737-600 B737-700 B737-800 B737-900 B737 B757-200 B757-300 B757F B757 MD90 MD80 CRJ-200 ERJ190 CRJ-700 CRJ-900 EMB145 ARJ21',
        '机型6(M0.6～0.69)':'DON328 BAE146-100 BAE146-300 BAE146',
        '机型5(M0.5～0.59)':'YN8 DHC8-300 DHC8-800 DHC8',
        '机型4(M0.4～0.49)':'YN7 MA60'
    }
    # 根据选择的选项执行操作
    st.write('该系列机型有:', type_dic[selected_option])
