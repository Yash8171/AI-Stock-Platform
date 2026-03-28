import os
import re

html_dir = r"c:\Users\sanja\OneDrive\Desktop\AI-Powered Stock & ETF Signal\static"

from html.parser import HTMLParser

class DivCounter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.div_depth = 0
        self.last_div_close = -1
        self.output = []
        self.in_main = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.in_main = True
        if self.in_main and tag == 'div':
            self.div_depth += 1

    def handle_endtag(self, tag):
        if tag == 'main':
            self.in_main = False
        if self.in_main and tag == 'div':
            self.div_depth -= 1


for filename in os.listdir(html_dir):
    if not filename.endswith(".html"): continue
    filepath = os.path.join(html_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # cache busting style.css
    content = re.sub(
        r'<link\s+rel="stylesheet"\s+href="css/style\.css(\?v=\d+)?"\s*>',
        r'<link rel="stylesheet" href="css/style.css?v=5">',
        content
    )

    # We will simply parse the file to find if there are too many </div> before </main>
    # Since the structure is quite simple, we can find <main... and </main>
    # then count <div> and </div> inside.
    main_start = re.search(r'<main[^>]*>', content)
    main_end = re.search(r'</main>', content)
    
    if main_start and main_end:
        main_content = content[main_start.end():main_end.start()]
        divs_open = len(re.findall(r'<div[^>]*>', main_content))
        divs_close = len(re.findall(r'</div>', main_content))
        
        diff = divs_close - divs_open
        
        if diff > 0:
            print(f"{filename}: Found {diff} extra </div> in <main>!")
            # Remove the last `diff` occurrences of </div> inside main
            
            parts = content.split('</main>')
            pre_main = parts[0]
            for _ in range(diff):
                # Reverse replace 1 occurrence of </div>
                pre_main = re.sub(r'</div>(?=[^<]*$)', '', pre_main)
            
            content = pre_main + '</main>' + parts[1]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Done.")
