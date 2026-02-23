from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import math

app = Flask(__name__)
CORS(app)

# 천간 (Heavenly Stems)
HEAVENLY_STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']

# 지지 (Earthly Branches)
EARTHLY_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 천간 오행
STEM_ELEMENTS = {
    '甲': 'Wood', '乙': 'Wood',
    '丙': 'Fire', '丁': 'Fire',
    '戊': 'Earth', '己': 'Earth',
    '庚': 'Metal', '辛': 'Metal',
    '壬': 'Water', '癸': 'Water'
}

# 지지 오행
BRANCH_ELEMENTS = {
    '子': 'Water', '丑': 'Earth', '寅': 'Wood', '卯': 'Wood',
    '辰': 'Earth', '巳': 'Fire', '午': 'Fire', '未': 'Earth',
    '申': 'Metal', '酉': 'Metal', '戌': 'Earth', '亥': 'Water'
}

# 지지 장간 (Hidden Stems in Branches)
HIDDEN_STEMS = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '戊', '庚'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲']
}

# 절기 계산 (Solar Term calculation)
def calculate_lichun(year):
    """
    입춘(立春) 계산 - 태양황경 315도
    근사 공식 사용 (정확도 ±1일)
    """
    # 기준: 2000년 입춘 = 2월 4일 20:32 (KST)
    base_year = 2000
    base_date = datetime(2000, 2, 4, 20, 32)
    
    # 1년 = 365.2422일
    years_diff = year - base_year
    days_diff = years_diff * 365.2422
    
    lichun = base_date + timedelta(days=days_diff)
    
    # 윤년 보정
    leap_correction = (year - base_year) // 4 - (base_year - base_year) // 4
    lichun = lichun - timedelta(days=leap_correction * 0.25)
    
    return lichun

def get_solar_term_for_month(year, month):
    """
    월주 결정을 위한 절기 확인
    입춘 기준으로 월이 바뀜
    """
    # 절기 월 시작 (양력 근사)
    solar_terms = {
        2: ('立春', 4),   # 2월 4일경
        3: ('驚蟄', 5),   # 3월 5일경
        4: ('淸明', 5),   # 4월 5일경
        5: ('立夏', 5),   # 5월 5일경
        6: ('芒種', 6),   # 6월 6일경
        7: ('小暑', 7),   # 7월 7일경
        8: ('立秋', 8),   # 8월 8일경
        9: ('白露', 8),   # 9월 8일경
        10: ('寒露', 8),  # 10월 8일경
        11: ('立冬', 8),  # 11월 8일경
        12: ('大雪', 7),  # 12월 7일경
        1: ('小寒', 6)    # 1월 6일경
    }
    return solar_terms.get(month, ('立春', 4))

def get_year_pillar(year):
    """연주 계산"""
    base_year = 1984  # 甲子年
    stem_index = (year - base_year) % 10
    branch_index = (year - base_year) % 12
    return HEAVENLY_STEMS[stem_index] + EARTHLY_BRANCHES[branch_index]

def get_month_pillar(year, month, day):
    """
    월주 계산 - 절기 고려
    """
    # 절기 확인
    term_name, term_day = get_solar_term_for_month(year, month)
    
    # 절기 이전이면 전월로 계산
    actual_month = month
    if day < term_day:
        actual_month = month - 1
        if actual_month < 1:
            actual_month = 12
            year = year - 1
    
    # 월주 계산
    year_stem_index = (year - 4) % 10
    
    # 정월(인월)은 3번째 지지 (寅)
    month_branch_index = (actual_month + 1) % 12
    
    # 월간 계산 (오호법)
    month_stem_base = (year_stem_index % 5) * 2
    month_stem_index = (month_stem_base + actual_month - 1) % 10
    
    return HEAVENLY_STEMS[month_stem_index] + EARTHLY_BRANCHES[month_branch_index]

def get_day_pillar(year, month, day):
    """
    일주 계산 - 정확한 만년력 기준
    기준일: 1900년 1월 1일 = 甲辰일
    """
    base_date = datetime(1900, 1, 1)
    target_date = datetime(year, month, day)
    days_diff = (target_date - base_date).days
    
    # 1900.1.1 = 甲辰 (천간 0, 지지 4)
    stem_index = (0 + days_diff) % 10
    branch_index = (4 + days_diff) % 12
    
    return HEAVENLY_STEMS[stem_index] + EARTHLY_BRANCHES[branch_index]

def get_hour_pillar(day_stem_index, hour, minute):
    """
    시주 계산 - 2시간 단위
    23:00-00:59 = 子時
    01:00-02:59 = 丑時
    ...
    """
    # 시간 지지 결정
    total_minutes = hour * 60 + minute
    
    # 23:00(1380분) 이상이면 다음날 子時
    if total_minutes >= 1380:  # 23:00
        hour_branch_index = 0  # 子
    else:
        # 2시간 단위로 지지 결정
        hour_branch_index = ((hour + 1) // 2) % 12
    
    # 시간 천간 계산 (일간에 따라 결정)
    day_to_hour_stem = {
        0: 0, 5: 0,  # 甲/己日
        1: 2, 6: 2,  # 乙/庚日
        2: 4, 7: 4,  # 丙/辛日
        3: 6, 8: 6,  # 丁/壬日
        4: 8, 9: 8   # 戊/癸日
    }
    
    hour_stem_base = day_to_hour_stem.get(day_stem_index, 0)
    hour_stem_index = (hour_stem_base + hour_branch_index) % 10
    
    return HEAVENLY_STEMS[hour_stem_index] + EARTHLY_BRANCHES[hour_branch_index]

def analyze_five_elements(year_p, month_p, day_p, hour_p):
    """
    오행 분석 - 천간 + 지지 + 장간 모두 고려
    """
    elements = {'Wood': 0, 'Fire': 0, 'Earth': 0, 'Metal': 0, 'Water': 0}
    
    pillars = [year_p, month_p, day_p, hour_p]
    
    for pillar in pillars:
        stem = pillar[0]  # 천간
        branch = pillar[1]  # 지지
        
        # 천간 오행 (가중치 1.0)
        if stem in STEM_ELEMENTS:
            elements[STEM_ELEMENTS[stem]] += 1.0
        
        # 지지 오행 (가중치 0.5)
        if branch in BRANCH_ELEMENTS:
            elements[BRANCH_ELEMENTS[branch]] += 0.5
        
        # 지지 장간 오행 (가중치 0.3)
        if branch in HIDDEN_STEMS:
            for hidden_stem in HIDDEN_STEMS[branch]:
                if hidden_stem in STEM_ELEMENTS:
                    elements[STEM_ELEMENTS[hidden_stem]] += 0.3
    
    # 가장 적은 원소 찾기 (동점이면 순서대로)
    min_value = min(elements.values())
    element_order = ['Wood', 'Fire', 'Earth', 'Metal', 'Water']
    missing = next(e for e in element_order if elements[e] == min_value)
    
    # 정수로 반올림하여 표시
    elements_display = {k: round(v, 1) for k, v in elements.items()}
    
    return elements_display, missing

@app.route('/health')
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/calculate', methods=['POST'])
@app.route('/api/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data.get('hour', 12))
        minute = int(data.get('minute', 0))
        
        # 연주
        year_pillar = get_year_pillar(year)
        
        # 월주 (절기 고려)
        month_pillar = get_month_pillar(year, month, day)
        
        # 일주 (정확한 계산)
        day_pillar = get_day_pillar(year, month, day)
        
        # 시주
        day_stem = day_pillar[0]
        day_stem_index = HEAVENLY_STEMS.index(day_stem)
        hour_pillar = get_hour_pillar(day_stem_index, hour, minute)
        
        # 오행 분석 (천간+지지+장간)
        elements, missing = analyze_five_elements(
            year_pillar, month_pillar, day_pillar, hour_pillar
        )
        
        # 일간 오행
        day_master_element = STEM_ELEMENTS[day_stem]
        
        # 음양 구분
        day_stem_idx = HEAVENLY_STEMS.index(day_stem)
        yin_yang = 'Yang' if day_stem_idx % 2 == 0 else 'Yin'
        
        result = {
            'pillars': {
                'year': year_pillar,
                'month': month_pillar,
                'day': day_pillar,
                'hour': hour_pillar
            },
            'day_master': day_stem,
            'day_master_element': day_master_element,
            'day_master_yin_yang': yin_yang,
            'five_elements': elements,
            'missing_element': missing,
            'calculation_method': 'accurate_with_solar_terms_and_hidden_stems'
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
