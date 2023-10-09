
import pandas as pd
import requests
from PIL import Image
import streamlit as st
from streamlit_lottie import st_lottie
import shutil
from datetime import date
import subprocess
import sys
import platform
import webbrowser
import base64
import sqlite3

if __name__ == "__main__":
    st.set_page_config(page_title="new_line_analyze", page_icon="🏠")
    st.title('这是主页')
    # 初始化全局配置
    if 'first_visit' not in st.session_state:
        st.session_state.data=pd.DataFrame([])
        st.session_state.choosedata=pd.DataFrame([])
        st.session_state.anadf=pd.DataFrame([])
        st.session_state.stardard=pd.DataFrame([])
        st.balloons()
    else:
        st.session_state.first_visit=False
        
