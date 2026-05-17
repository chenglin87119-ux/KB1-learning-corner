#!/usr/bin/env python3
"""Batch modify all unit HTML files."""
import os
import glob
import re

html_dir = "/home/wlsclaw/ket_learning_corner/html"
files = sorted(glob.glob(os.path.join(html_dir, "unit*.html")))

NEW_CSS_BLOCK = """    /* 单词卡片 - 新设计 */
    .word-card {
      background: linear-gradient(145deg, #ffffff, #f8f9ff);
      border: 3px solid #e8eaff;
      border-radius: 20px;
      padding: 16px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.08);
      transition: transform 0.3s;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
    }
    .word-card:hover {
      transform: scale(1.06);
    }
    .word-card .emoji {
      font-size: 2.2em;
      margin-bottom: 4px;
    }
    .word-card .english {
      font-size: 1.3em;
      font-weight: bold;
      color: #5c6bc0;
    }
    .word-card .chinese {
      font-size: 0.95em;
      color: #78909c;
      margin-top: 4px;
    }
    .word-card .example-area {
      margin-top: 8px;
      padding: 8px 12px;
      background: #fff8e1;
      border-radius: 12px;
      font-size: 0.9em;
      color: #e65100;
      width: 100%;
    }
    .speaker-btn {
      display: inline-block;
      font-size: 1.8em;
      cursor: pointer;
      margin-left: 6px;
      transition: transform 0.2s;
      line-height: 1;
    }
    .speaker-btn:hover { transform: scale(1.25); }
    .speaker-btn:active { transform: scale(0.9); }
    .speaker-btn.speaking { animation: speakPulse 0.5s ease-in-out 3; }
    @keyframes speakPulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.3); }
    }
    .sentence-box .en .speaker-btn {
      font-size: 1.4em;
      vertical-align: middle;
    }"""

NEW_RENDER = """  function renderCards(data, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    data.forEach((word, index) => {
      const card = document.createElement('div');
      card.className = 'word-card';
      card.innerHTML = `
        <div class="emoji">${word.emoji}</div>
        <div class="english">${word.en}<span class="speaker-btn" onclick="event.stopPropagation();speakWord('${word.en}')">🔊</span></div>
        <div class="chinese">${word.cn}</div>
        <div class="example-area">💬 ${word.example} <span class="speaker-btn" onclick="event.stopPropagation();speakWord('${word.example}')">🔊</span></div>
      `;
      container.appendChild(card);
    });
  }"""

SPEAK_FUNC = """  // ========== 🔊 发音功能（ResponsiveVoice） ==========
  function speakWord(text) {
    responsiveVoice.speak(text, "UK English Female", {rate: 0.8});
  }"""

# Old speakWord in unit1 (speechSynthesis version)
OLD_SPEAK_UNIT1 = """  // ========== 🔊 发音功能（Web Speech API） ==========
  // 使用浏览器自带的语音合成，语速0.8适合小朋友模仿
  function speakWord(text) {
    if (!window.speechSynthesis) {
      alert('你的浏览器不支持发音功能，请试试 Chrome 浏览器哦～😊');
      return;
    }
    // 取消正在播放的语音
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';    // 美式英语发音
    utterance.rate = 0.8;        // 语速放慢，适合小朋友
    utterance.pitch = 1.1;       // 音调略高，更友好
    utterance.volume = 1;
    window.speechSynthesis.speak(utterance);
  }"""


def extract_until(pattern_start, content, from_pos):
    """Find a pattern and extract content from `from_pos` until the line after the pattern."""
    pos = content.find(pattern_start, from_pos)
    if pos < 0:
        return None, -1
    end = content.find('\n', pos)
    if end < 0:
        end = len(content)
    return content[pos:end+1], end + 1

def find_func_end(content, start_pos):
    """Find the closing brace position of a function starting at start_pos."""
    brace_count = 0
    in_string = False
    in_template = False
    string_char = None
    
    for i in range(start_pos, len(content)):
        ch = content[i]
        if ch == '`' and not in_string:
            in_template = not in_template
        elif ch in '"\'' and not in_template:
            if not in_string:
                in_string = True
                string_char = ch
            elif ch == string_char:
                in_string = False
        elif not in_string and not in_template:
            if ch == '{':
                brace_count += 1
            elif ch == '}':
                brace_count -= 1
                if brace_count == 0:
                    return i + 1
    return len(content)

def find_render_func(content):
    """Find and return (start, end) of the renderCards function."""
    idx = content.find('function renderCards')
    if idx < 0:
        return None
    end = find_func_end(content, idx)
    return (idx, end)

def find_checkblank_functions(content):
    """Find all checkBlank functions and return list of (start, end) tuples."""
    functions = []
    search_from = 0
    while True:
        idx = content.find('function checkBlank', search_from)
        if idx < 0:
            break
        end = find_func_end(content, idx)
        functions.append((idx, end))
        search_from = end
    return functions

def add_empty_check(text, func_text):
    """Add empty-input check to a checkBlank function if not already present."""
    if 'if (!input)' in func_text:
        return func_text
    
    # Find input and fb lines
    input_match = re.search(r"const input = document\.getElementById\('blank\d+'\)\.value\.trim\(\)", func_text)
    fb_match = re.search(r"const fb = document\.getElementById\('feedback\d+'\)", func_text)
    
    if not input_match or not fb_match:
        return func_text
    
    # Insert empty check right after the fb declaration line
    fb_line_end = func_text.find('\n', fb_match.end())
    if fb_line_end < 0:
        fb_line_end = len(func_text)
    
    empty_check = """    if (!input) {
      fb.innerHTML = '✏️ 在这里写下你的答案吧～';
      fb.className = 'feedback';
      fb.style.color = '#999';
      return;
    }
"""
    return func_text[:fb_line_end+1] + empty_check + func_text[fb_line_end+1:]


for fp in files:
    fn = os.path.basename(fp)
    print(f"\n=== {fn} ===")
    
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    orig = content
    
    # 1. Add responsiveVoice script before </head>
    if 'responsivevoice.org' not in content:
        content = content.replace('</head>', '  <script src="https://code.responsivevoice.org/responsivevoice.js"></script>\n</head>', 1)
        print("  [OK] Added responsiveVoice script")
    
    # 2. Replace old word-card CSS with new flat design
    # Find the CSS block from the comment to the next section
    css_start_markers = ['/* 单词卡片 - 正面 */', '/* 单词卡片 */', '/* 单词卡片', '/* 单词卡片 - 新设计 */']
    css_start = -1
    for marker in css_start_markers:
        pos = content.find(marker)
        if pos >= 0:
            css_start = pos
            break
    
    if css_start >= 0 and 'word-card-inner' in content[css_start:css_start+1000]:
        # We found old flip-card CSS to replace
        # Find the end - it's the next section comment
        next_section = content.find('/* 单词分类标签', css_start)
        if next_section < 0:
            # Try other section markers
            for m in ['/* 单词分类标签', '/* 第二部分', '/* ========== 第二部分']:
                ns = content.find(m, css_start)
                if ns > 0:
                    next_section = ns
                    break
        
        if next_section > css_start:
            # Also check for .tap-hint which should be within this range
            content = content[:css_start] + NEW_CSS_BLOCK + '\n' + content[next_section:]
            print("  [OK] Replaced flip-card CSS")
        else:
            print("  [WARN] Could not find section boundary for CSS")
    else:
        print("  [SKIP] No old flip-card CSS found")
    
    # 3. Replace renderCards function
    render_range = find_render_func(content)
    if render_range:
        start, end = render_range
        old_render = content[start:end]
        if 'word-card-inner' in old_render or 'flipped' in old_render or 'tap-hint' in old_render:
            content = content[:start] + NEW_RENDER + content[end:]
            print("  [OK] Replaced renderCards function")
        else:
            print("  [SKIP] renderCards already updated")
    else:
        print("  [WARN] No renderCards function found")
    
    # 4. Handle speakWord function
    if fn == 'unit1_hello.html':
        if 'speechSynthesis' in content:
            old_start = content.find('// ========== 🔊 发音功能（Web Speech API）')
            if old_start >= 0:
                # Find the speechSynthesis speakWord function
                func_start = content.find('function speakWord', old_start)
                if func_start >= 0:
                    func_end = find_func_end(content, func_start)
                    # Remove everything from the comment to end of function
                    # Include trailing blank lines
                    end_pos = func_end
                    while end_pos < len(content) and content[end_pos] in '\n\r ':
                        end_pos += 1
                    content = content[:old_start] + SPEAK_FUNC + '\n' + content[end_pos:]
                    print("  [OK] Replaced speechSynthesis speakWord")
                else:
                    print("  [WARN] Could not find speakWord function in unit1")
            else:
                print("  [SKIP] No old speechSynthesis section")
        else:
            print("  [SKIP] speechSynthesis not present")
    else:
        if 'speakWord' not in content:
            # Insert before checkBlank functions
            insert_marker = '// ========== 📝 填空练习逻辑 =========='
            insert_pos = content.find(insert_marker)
            if insert_pos < 0:
                insert_pos = content.find('function checkBlank1')
            if insert_pos > 0:
                line_start = content.rfind('\n', 0, insert_pos) + 1
                content = content[:line_start] + SPEAK_FUNC + '\n\n' + content[line_start:]
                print("  [OK] Added speakWord function")
            else:
                print("  [WARN] Could not find insertion point")
        else:
            print("  [SKIP] speakWord already present")
    
    # 5. Replace ✅ 检查 with 🔍 检查
    if '✅ 检查' in content:
        content = content.replace('✅ 检查', '🔍 检查')
        print("  [OK] Replaced ✅ 检查 with 🔍 检查")
    
    # 6. Add empty-input checks to checkBlank functions
    check_funcs = find_checkblank_functions(content)
    if check_funcs:
        modified_count = 0
        for start, end in reversed(check_funcs):
            old_func = content[start:end]
            new_func = add_empty_check(content, old_func)
            if new_func != old_func:
                content = content[:start] + new_func + content[end:]
                modified_count += 1
        print(f"  [OK] Updated {modified_count}/{len(check_funcs)} checkBlank functions")
    else:
        print("  [WARN] No checkBlank functions found")
    
    # Save if changed
    if content != orig:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  => Saved")
    else:
        print("  => No changes")

print("\n=== ALL DONE ===")
