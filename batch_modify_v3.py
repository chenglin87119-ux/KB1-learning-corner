#!/usr/bin/env python3
"""v3 - Fixed find_func_end to handle escape sequences in strings."""
import os, glob, re

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


def find_next_brace(content, start):
    """Find the matching closing brace for the opening brace at start-1.
    Properly handles strings and escape sequences."""
    i = start
    depth = 1
    in_string = False
    in_template = False
    string_char = None
    
    while i < len(content) and depth > 0:
        ch = content[i]
        
        # Handle escape sequences
        if ch == '\\' and (in_string or in_template):
            i += 2  # Skip the escaped character
            continue
        
        if ch == '`' and not in_string:
            in_template = not in_template
        elif (ch == "'" or ch == '"') and not in_template:
            if not in_string:
                in_string = True
                string_char = ch
            elif ch == string_char:
                in_string = False
        elif not in_string and not in_template:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    return i


def find_func_end(content, start_pos):
    """Find the closing brace position of a function starting at start_pos."""
    # Find the opening brace
    brace_pos = content.find('{', start_pos)
    if brace_pos < 0:
        return len(content)
    return find_next_brace(content, brace_pos + 1)


def has_standalone_speakword(content):
    """True if a proper speakWord function exists outside template strings."""
    idx = content.find('function speakWord')
    if idx < 0:
        return False
    before = content[max(0,idx-200):idx]
    backtick_count = before.count('`')
    return backtick_count % 2 == 0


for fp in files:
    fn = os.path.basename(fp)
    print(f"\n=== {fn} ===")
    
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    
    # 1. Add responsiveVoice script
    if 'responsivevoice.org' not in content:
        content = content.replace('</head>', '  <script src="https://code.responsivevoice.org/responsivevoice.js"></script>\n</head>', 1)
        print("  [OK] Added responsiveVoice script")
    
    # 2. Replace old word-card CSS
    if 'word-card-inner' in content:
        card_pos = content.find('.word-card {')
        if card_pos >= 0:
            line_start = content.rfind('\n', 0, card_pos) + 1
            next_section = content.find('\n    /* 单词分类标签', line_start)
            if next_section < 0:
                next_section = content.find('/* 单词分类标签', line_start)
            if next_section < 0:
                next_section = len(content)
            content = content[:line_start] + NEW_CSS_BLOCK + '\n' + content[next_section:]
            print("  [OK] Replaced flip-card CSS")
        else:
            print("  [WARN] No .word-card { found")
    else:
        print("  [SKIP] No flip-card CSS")
    
    # 3. Replace renderCards function
    render_idx = content.find('function renderCards')
    if render_idx >= 0:
        end = find_func_end(content, render_idx)
        old_render = content[render_idx:end]
        if 'word-card-inner' in old_render or 'tap-hint' in old_render:
            content = content[:render_idx] + NEW_RENDER + content[end:]
            print("  [OK] Replaced renderCards function")
        else:
            print("  [SKIP] renderCards already updated")
    else:
        print("  [WARN] No renderCards function")
    
    # 4. Handle speakWord
    if fn == 'unit1_hello.html':
        if 'speechSynthesis' in content:
            old_start = content.find('// ========== 🔊 发音功能（Web Speech API）')
            if old_start >= 0:
                func_start = content.find('function speakWord', old_start)
                if func_start >= 0:
                    func_end = find_func_end(content, func_start)
                    end_pos = func_end
                    while end_pos < len(content) and content[end_pos] in '\n\r ':
                        end_pos += 1
                    content = content[:old_start] + SPEAK_FUNC + '\n' + content[end_pos:]
                    print("  [OK] Replaced speechSynthesis speakWord")
                else:
                    print("  [WARN] speakWord not found near speechSynthesis")
            else:
                print("  [SKIP] No Web Speech API section")
    else:
        if not has_standalone_speakword(content):
            insert_marker = '// ========== 📝 填空练习逻辑 =========='
            insert_pos = content.find(insert_marker)
            if insert_pos < 0:
                insert_pos = content.find('function checkBlank1')
            if insert_pos > 0:
                line_start = content.rfind('\n', 0, insert_pos) + 1
                content = content[:line_start] + SPEAK_FUNC + '\n\n' + content[line_start:]
                print("  [OK] Added speakWord function")
            else:
                print("  [WARN] No insertion point for speakWord")
        else:
            print("  [SKIP] speakWord already present")
    
    # 5. Replace ✅ 检查 with 🔍 检查
    count_check = content.count('✅ 检查')
    if count_check > 0:
        content = content.replace('✅ 检查', '🔍 检查')
        print(f"  [OK] Replaced {count_check} ✅ 检查 with 🔍 检查")
    
    # 6. Add empty-input checks to checkBlank functions
    search_pos = 0
    check_funcs = []
    while True:
        idx = content.find('function checkBlank', search_pos)
        if idx < 0:
            break
        end = find_func_end(content, idx)
        check_funcs.append((idx, end))
        search_pos = end
    
    modified_count = 0
    for start, end in reversed(check_funcs):
        old_func = content[start:end]
        if 'if (!input)' in old_func:
            continue
        
        # Check for 'else' after correct check pattern - handle properly
        input_match = re.search(r"const input = document\.getElementById\('blank\d+'\)\.value\.trim\(\)", old_func)
        fb_match = re.search(r"const fb = document\.getElementById\('feedback\d+'\)", old_func)
        
        if not input_match or not fb_match:
            print(f"  [WARN] Could not parse checkBlank function at position {start}")
            continue
        
        fb_line_end = old_func.find('\n', fb_match.end())
        if fb_line_end < 0:
            fb_line_end = len(old_func)
        
        empty_check = """    if (!input) {
      fb.innerHTML = '✏️ 在这里写下你的答案吧～';
      fb.className = 'feedback';
      fb.style.color = '#999';
      return;
    }
"""
        new_func = old_func[:fb_line_end+1] + empty_check + old_func[fb_line_end+1:]
        content = content[:start] + new_func + content[end:]
        modified_count += 1
    
    print(f"  [OK] Updated {modified_count}/{len(check_funcs)} checkBlank functions")
    
    if content != orig:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  => Saved")
    else:
        print("  => No changes")

print("\n=== ALL DONE ===")
