import streamlit as st
import requests
import json
from datetime import datetime, timedelta, date
import time
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 페이지 기본 설정
st.set_page_config(
    page_title="한우산 별천지 숙박 빈방 찾기",
    page_icon="🏕️",
    layout="wide"
)

# 고정 설정 값
PLACE_ID = "4379536846"
DEFAULT_COOKIE = "NAC=nyNtBExYI7RX; NNB=K2A64S2MWYDGU; bnb_tooltip_shown_finance_v1=true; _fbp=fb.1.1780312272093.69699559161814351; ab.storage.userId.7d7bb94a-f465-48e5-bec1-35db97daf128=g%3A3fvJh%7Ce%3Aundefined%7Cc%3A1780395206595%7Cl%3A1780395206597; ab.storage.deviceId.7d7bb94a-f465-48e5-bec1-35db97daf128=g%3A796f7ab8-f621-227e-6436-a010f7f8af13%7Ce%3Aundefined%7Cc%3A1780395206599%7Cl%3A1780395206599; ab.storage.sessionId.7d7bb94a-f465-48e5-bec1-35db97daf128=g%3A1dbcc849-956e-725a-6d14-96ea41d8b513%7Ce%3A1780397194261%7Cc%3A1780395206596%7Cl%3A1780395394261; ba.uuid=a5935baf-528e-4e05-938c-34cf0682a071; tooltipDisplayed=true; ASID=77c7de840000019ecb91d4a30000001d; _ga=GA1.2.1425938226.1783603618; NV_WETR_LAST_ACCESS_RGN_M=\"MDQxMTMzNjA=\"; NV_WETR_LOCATION_RGN_M=\"MDQxMTMzNjA=\"; nid_inf=-1250604521; NID_AUT=XGg/xpiQz3cd/y2zgV4vWFJ3dChoy0YiL005zKTVVphWzWtQPW4J5bT6mcyS5isc; _gid=GA1.2.1287303399.1787223173; _ga_6Z6DP60WFK=GS2.2.s1787223173$o1$g1$t1787223189$j44$l0$h0; SRT30=1787283240; SRT5=1787285946; page_uid=joQf2dqosussshGoCH0-394107; PLACE_LANGUAGE=ko; NID_SES=AAAB1yYI+O0I4B18F6eiZ2zeFz6Vh/xVbhdhI5cGDiziHS0FkYMq9OQilOuCcX1Hx5Nt+xvw01ce6amLFqNdnxyayfRw6qGmsJklz7xQH8SfgGcLWtjN4Tfvq9hZbhXsUyfm2iovbO0kdmF4h3TLCfR9oTX0xLvdACIrDxVWaLmJDMMpQjtdb7N/NxVL4jQQTdbaECMwWqcE25BG2+ZUacbVxSaFVlMh13Zq+7e0eY5PHT+LBJYRFompwGMt5S2vKY3Rgv17tAJDv0giqumoCMhqZCjTQ4gIrA6sPUf+cWf746Dl9ZCMv4miIABTjdP1b3iPdgJDrmH2ZkkGhQ0KhLCFZsHre0juFUGpYdhQugcbXKdHrbrQ8pC0OlQA0xxdPUiireNBnqiapWZmeZEYbXoqGSUHHXYZV7/4Ap30i2uNRmRxovai6yUlPI9s4X/9uN+FPi/XN7gLPog1/Ec4fhDX/aAAlAQjn8N0Qx0AyIjnhVYY6iWmVmo3CDVBvt9z8aT6jDkXGCpiWi4HPg14fldxzOdzFPuZB5JqpU1RWc9cwPzeqV5yfD/c42C1Gk1zxUv7jRIyHjcOJg7hgz0gDLq8HmUBaJ4X29UAwHsaQn0sHex1ldfi3rRSbmVwbRyXeJVG7A==; MM_PF=SEARCH; BUC=qLVcfRYKCWuoAQzSw-jftVi4BQQ3kOkD_ynxsx4N59A="
DEFAULT_NCAPTCHA_TOKEN = "zq4HnOHinjKeTqYEwAjeiUbJ0dmlI0StXJafis__rj4="

QUERY = """
query bookingDetails($input: AccommodationBookingDetailsInput) {
  accommodationBookingDetails(input: $input) {
    ...AccommodationBookingDetails
    __typename
  }
}

fragment AccommodationBookingDetails on AccommodationBookingDetails {
  roomTotal
  siteDesc
  agencyName
  images
  businessTypeId
  rooms {
    reprUrl
    resrvUrl
    drtOptionList {
      iconName
      optionName
      __typename
    }
    isBookable
    isMatching
    bookingType
    resocId
    resocName
    resocDesc
    cond2Val
    cond3Val
    subImage
    excptMsg
    minPrice
    maxPrice
    index
    todayDealRate
    discountText
    priceInfo {
      off_friday
      off_weekday
      off_weekend
      on_friday
      on_weekday
      on_weekend
      peak_friday
      peak_weekday
      peak_weekend
      __typename
    }
    isNPayUsed
    nPayRegStatusCode
    bizItemSubType
    minBookingTime
    accommodationAdditionalProperty {
      checkInTime
      checkOutTime
      isFixedRoomComposition
      roomCompositions {
        name
        bedroomCompositions {
          name
          type
          bunkBed
          kingBed
          queenBed
          doubleBed
          singleBed
          beddingSet
          familyBed
          sofaBed
          isStudioRoom
          __typename
        }
        bathroomCompositions {
          name
          isPrivate
          __typename
        }
        campingSiteCompositions {
          name
          type
          width
          height
          floorType
          isCaravanAccessible
          isTrailerAccessible
          parkingPositionType
          __typename
        }
        __typename
      }
      roomType
      __typename
    }
    __typename
  }
  __typename
}
"""

def format_price(price):
    if not price:
        return "-"
    try:
        return f"{int(price):,}"
    except:
        return str(price)

def check_availability(checkin_date, checkout_date, guest=2):
    category_quoted = quote('pension')
    referer_url = f"https://pcmap.place.naver.com/accommodation/{PLACE_ID}/room?fromPanelNum=1&additionalHeight=76&timestamp=202608211341&locale=ko&svcName=map_pcv5&entry=bmp&level=top&businessCategory={category_quoted}&guest={guest}&checkin={checkin_date}&checkout={checkout_date}&filterType=%EC%97%85%EC%B2%B4&from=map"
    
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "cookie": DEFAULT_COOKIE,
        "origin": "https://pcmap.place.naver.com",
        "pragma": "no-cache",
        "referer": referer_url,
        "sec-ch-ua": '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "x-wtm-graphql": "eyJhcmciOiI0Mzc5NTM2ODQ2IiwidHlwZSI6ImFjY29tbW9kYXRpb24iLCJzb3VyY2UiOiJwbGFjZSJ9",
        "x-wtm-ncaptcha-token": DEFAULT_NCAPTCHA_TOKEN,
    }
    
    variables = {
        "input": {
            "businessId": PLACE_ID,
            "isNx": False,
            "checkin": checkin_date,
            "checkout": checkout_date,
            "entry": "bmp",
            "guest": str(guest),
            "size": 50
        }
    }
    
    payload = [{
        "operationName": "bookingDetails",
        "variables": variables,
        "query": QUERY
    }]
    
    try:
        response = requests.post(
            "https://pcmap-api.place.naver.com/graphql",
            headers=headers,
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                response_data = data[0]
                if "data" in response_data and "accommodationBookingDetails" in response_data["data"]:
                    return response_data["data"]["accommodationBookingDetails"], None
        return None, f"HTTP {response.status_code}"
    except Exception as e:
        return None, str(e)

def send_ntfy_alert(ntfy_channel, available_dates):
    if not ntfy_channel or not available_dates:
        return
    
    message = "🏕️ [한우산 별천지] 예약 가능한 객실이 발견되었습니다!\n\n"
    for date_info in available_dates:
        message += f"📅 {date_info['checkin']} ~ {date_info['checkout']}\n"
        message += f"🏠 {date_info['room_name']}\n"
        message += f"💰 {date_info['min_price']} ~ {date_info['max_price']}원\n"
        message += f"🔗 {date_info['url']}\n\n"
    message += "⚠️ 빠르게 예약하세요!"
    
    try:
        requests.post(
            f"https://ntfy.sh/{ntfy_channel}",
            data=message.encode('utf-8'),
            headers={
                "Title": f"🏕️ 한우산 별천지 {len(available_dates)}개 날짜 빈방!",
                "Priority": "high",
                "Tags": "tent,camping"
            },
            timeout=3
        )
    except Exception:
        pass

def render_results(found_dates):
    st.subheader(f"✨ 찾은 빈방 ({len(found_dates)}개)")
    if found_dates:
        cols = st.columns(3)
        for idx, (k, info) in enumerate(found_dates.items()):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### 📅 {info['checkin']} ~ {info['checkout']}")
                    st.markdown(f"**🏠 객실:** {info['room_name']}")
                    st.markdown(f"**💰 가격:** {info['min_price']} ~ {info['max_price']}원")
                    st.link_button("👉 바로 예약하러 가기", info['url'], use_container_width=True)

# --- UI 레이아웃 ---
st.title("🏕️ 한우산 별천지 숙박 빈방 찾기")

with st.sidebar:
    st.header("⚙️ 모니터링 설정")
    
    today = date.today()
    start_date = st.date_input("시작일", today + timedelta(days=1))
    end_date = st.date_input("종료일", today + timedelta(days=10))
    
    nights = st.number_input("숙박 박수 (N박)", min_value=1, value=1)
    guests = st.number_input("인원 수", min_value=1, value=2)
    poll_interval = st.number_input("폴링 간격 (초)", min_value=10, value=30)
    
    ntfy_channel = st.text_input("ntfy 알림 채널명 (선택)", value="", help="https://ntfy.sh/채널명 형식에서 채널명 입력")

if "monitoring" not in st.session_state:
    st.session_state.monitoring = False
if "found_dates" not in st.session_state:
    st.session_state.found_dates = {}
if "notified_keys" not in st.session_state:
    st.session_state.notified_keys = set()

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🚀 모니터링 시작", use_container_width=True, type="primary", disabled=st.session_state.monitoring):
        if start_date >= end_date:
            st.error("종료일은 시작일보다 이후여야 합니다.")
        else:
            st.session_state.monitoring = True
            st.session_state.found_dates = {}
            st.session_state.notified_keys = set()
            st.rerun()

with col2:
    if st.button("⏹️ 중지", use_container_width=True, disabled=not st.session_state.monitoring):
        st.session_state.monitoring = False
        st.rerun()

status_box = st.empty()
results_box = st.empty()

if st.session_state.monitoring:
    date_list = []
    curr = start_date
    while curr <= end_date:
        checkout = curr + timedelta(days=nights)
        if checkout <= end_date:
            date_list.append({
                'checkin': curr.strftime("%Y%m%d"),
                'checkout': checkout.strftime("%Y%m%d")
            })
        curr += timedelta(days=1)

    attempt = 0

    while st.session_state.monitoring:
        attempt += 1
        
        pending = [
            d for d in date_list 
            if f"{d['checkin']}_{d['checkout']}" not in st.session_state.found_dates
        ]
        
        if not pending:
            status_box.success("🎉 모든 날짜에서 빈방 조회가 완료되었습니다!")
            st.session_state.monitoring = False
            break

        status_box.info(f"[{datetime.now().strftime('%H:%M:%S')}] {attempt}회차 고속 조회의 결과를 불러오는 중... ({len(pending)}개 날짜)")
        
        newly_found_this_batch = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_date = {
                executor.submit(
                    check_availability, 
                    d['checkin'], 
                    d['checkout'], 
                    guests
                ): d for d in pending
            }
            
            for future in as_completed(future_to_date):
                date_info = future_to_date[future]
                checkin, checkout = date_info['checkin'], date_info['checkout']
                date_key = f"{checkin}_{checkout}"
                
                result, error = future.result()
                if result and "rooms" in result:
                    bookable = [r for r in result["rooms"] if r.get("isBookable") == True]
                    if bookable:
                        room = bookable[0]
                        date_info['room_name'] = room.get('resocName', '정보 없음')
                        date_info['min_price'] = format_price(room.get('minPrice'))
                        date_info['max_price'] = format_price(room.get('maxPrice'))
                        date_info['url'] = room.get('resrvUrl', '#')
                        
                        st.session_state.found_dates[date_key] = date_info
                        
                        if date_key not in st.session_state.notified_keys:
                            newly_found_this_batch.append(date_info)
                            st.session_state.notified_keys.add(date_key)

        if newly_found_this_batch:
            st.toast(f"🎉 {len(newly_found_this_batch)}개 날짜 빈방 발견!", icon="✅")
            if ntfy_channel:
                send_ntfy_alert(ntfy_channel, newly_found_this_batch)

        with results_box.container():
            render_results(st.session_state.found_dates)

        status_box.text(f"⏳ {poll_interval}초 후 다음 검사를 진행합니다...")
        time.sleep(poll_interval)

else:
    with results_box.container():
        render_results(st.session_state.found_dates)
