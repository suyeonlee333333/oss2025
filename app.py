import folium
import pandas as pd
from folium.plugins import MarkerCluster
import streamlit as st

# CSV 파일 읽기
df = pd.read_csv("night_pharmacy1.csv", encoding="utf-8-sig")

# 지도 초기화 (부산의 위도, 경도)
location = [35.1796, 129.0756]
m = folium.Map(location=location, zoom_start=12)

# 마커 클러스터 추가 (많은 마커를 한 번에 처리할 수 있도록)
marker_cluster = MarkerCluster().add_to(m)

# 필터링된 데이터 사용
for index, row in df.iterrows():
    # 팝업에 사용될 텍스트
    popup_text = f"""
    <b>{row['약국명']}</b><br>
    {row['소재지(도로명)']}<br>
    <b>전화:</b> {row['전화번호']}
    """

    # 마커에 팝업 추가
    folium.Marker(
        [row['위도'], row['경도']],
        popup=folium.Popup(popup_text, max_width=300, min_width=200),  # 팝업 스타일
        icon=folium.Icon(color='blue', icon='info-sign')  # 아이콘 추가
    ).add_to(marker_cluster)

# 지도 HTML 파일로 저장
map_path = "map.html"
m.save(map_path)

# Streamlit에서 지도 표시
st.markdown(f'<iframe src="{map_path}" width="100%" height="600px" style="border:none;"></iframe>', unsafe_allow_html=True)
