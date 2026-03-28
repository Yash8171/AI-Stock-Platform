import os
import re

html_dir = r"c:\Users\sanja\OneDrive\Desktop\AI-Powered Stock & ETF Signal\static"

for filename in os.listdir(html_dir):
    if filename.endswith(".html"):
        filepath = os.path.join(html_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update CSS version to v=5
        # Look for <link rel="stylesheet" href="css/style.css"> with or without ?v=...
        content = re.sub(
            r'<link\s+rel="stylesheet"\s+href="css/style\.css(\?v=\d+)?"\s*>',
            r'<link rel="stylesheet" href="css/style.css?v=5">',
            content
        )

        # Remove extra </div> at the end of <main>
        # A common pattern from the previous edits is adding an extra </div> before </main>.
        # Let's fix it by matching </div></div></div></main> -> </div></div></main> 
        # Actually it's better to just ensure the DOM is valid, but let's blindly fix 
        # \s*</div>\s*</div>\s*</div>\s*</main>  if we know it's there.
        # But wait, we saw one extra </div> in all files modified previously. 
        # The previous change added `</div>` to close `page-container` but some already had them.
        # Let's use `re.sub(r'(?:[ \t]*</div>\n){2,}[ \t]*</main>', r'            </div>\n        </main>', content)`
        # To be safe, let's print the files we change.

        new_content = re.sub(r'([ \t]*</div>\n)+([ \t]*</main>)', r'\n            </div>\n\2', content)

        if content != new_content:
            pass # we'll write it
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

print("Done updating HTML files.")
