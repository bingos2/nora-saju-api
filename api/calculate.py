from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# 천간
HEAVENLY_STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
# 지지
EARTHLY_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 오행
FIVE_ELEMENTS = {
    '甲': 'Wood', '乙': 'Wood',
    '丙': 'Fire', '丁': 'Fire',
    '戊': 'Earth', '己': 'Earth',
    '庚': 'Metal', '辛': 'Metal',
    '壬': 'Water', '癸': 'Water'
}

def get_year_pillar(year):
    base_year = 1984
    stem_index = (year - base_year) % 10
    branch_index = (year - base_year) % 12
    return HEAVENLY_STEMS[stem_index] + EARTHLY_BRANCHES[branch_index]

def get_month_pillar(year, month):
    year_stem_index = (year - 4) % 10
    month_stem_base = (year_stem_index % 5) * 2
    month_stem_index = (month_stem_base + month - 1) % 10
    month_branch_index = (month + 1) % 12
    return HEAVENLY_STEMS[month_stem_index] + EARTHLY_BRANCHES[month_branch_index]

def get_day_pillar(year, month, day):
    base_date = datetime(1900, 1, 1)
    target_date = datetime(year, month, day)
    days_diff = (target_date - base_date).days
    stem_index = (0 + days_diff) % 10
    branch_index = (4 + days_diff) % 12
    return HEAVENLY_STEMS[stem_index] + EARTHLY_BRANCHES[branch_index]

def get_hour_pillar(day_stem_index, hour):
    hour_branch_index = ((hour + 1) // 2) % 12
    day_to_hour_stem = {
        0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4,
        3: 6, 8: 6, 4: 8, 9: 8
    }
    hour_stem_base = day_to_hour_stem.get(day_stem_index, 0)
    hour_stem_index = (hour_stem_base + hour_branch_index) % 10
    return HEAVENLY_STEMS[hour_stem_index] + EARTHLY_BRANCHES[hour_branch_index]

def analyze_five_elements(year_p, month_p, day_p, hour_p):
    pillars = [year_p, month_p, day_p, hour_p]
    elements = {'Wood': 0, 'Fire': 0, 'Earth': 0, 'Metal': 0, 'Water': 0}
    for pillar in pillars:
        stem = pillar[0]
        if stem in FIVE_ELEMENTS:
            elements[FIVE_ELEMENTS[stem]] += 1
    missing = min(elements, key=elements.get)
    return elements, missing

def handler(request):
    """Vercel Serverless Function Handler"""
    if request.method == 'POST':
        try:
            data = request.json
            
            year = int(data['year'])
            month = int(data['month'])
            day = int(data['day'])
            hour = int(data.get('hour', 12))
            
            year_pillar = get_year_pillar(year)
            month_pillar = get_month_pillar(year, month)
            day_pillar = get_day_pillar(year, month, day)
            
            day_stem = day_pillar[0]
            day_stem_index = HEAVENLY_STEMS.index(day_stem)
            hour_pillar = get_hour_pillar(day_stem_index, hour)
            
            elements, missing = analyze_five_elements(
                year_pillar, month_pillar, day_pillar, hour_pillar
            )
            
            day_master_element = FIVE_ELEMENTS[day_stem]
            
            result = {
                'pillars': {
                    'year': year_pillar,
                    'month': month_pillar,
                    'day': day_pillar,
                    'hour': hour_pillar
                },
                'day_master': day_stem,
                'day_master_element': day_master_element,
                'five_elements': elements,
                'missing_element': missing
            }
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    elif request.method == 'GET':
        return jsonify({'status': 'ok'})
    
    return jsonify({'error': 'Method not allowed'}), 405
