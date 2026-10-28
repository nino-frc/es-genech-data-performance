with open('C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/generate_match_briefing.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace body style with double braces
old_body = """            body {{
                font-family: 'Montserrat', sans-serif;
                margin: 0;
                padding: 24px 28px;
                background-color: #ede8d8;
                color: #0a1728;
                width: 1080px;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}"""

new_body = """            html, body {{
                font-family: 'Montserrat', sans-serif;
                margin: 0;
                padding: 26px 30px;
                background-color: #ede8d8;
                color: #0a1728;
                width: 1080px;
                height: 1920px;
                max-height: 1920px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                overflow: hidden;
            }}"""

if old_body in code:
    code = code.replace(old_body, new_body)
    print('Replaced body in generate_match_briefing.py')
else:
    print('old_body still not found!')

with open('C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/generate_match_briefing.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Done!')
