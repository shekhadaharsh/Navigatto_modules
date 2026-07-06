import os
import re

folders = [
    r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src\components",
    r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src\modals",
    r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src"
]

for folder in folders:
    for root, dirs, files in os.walk(folder):
        if "node_modules" in root:
            continue
        for f in files:
            if not f.endswith(".jsx"):
                continue
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
            
            # Find all capitalized JSX tags like <ShieldCheck or <Gauge
            jsx_tags = set(re.findall(r'<([A-Z][a-zA-Z0-9_]*)', content))
            
            # Ignore built-ins or standard
            jsx_tags.discard('React')
            jsx_tags.discard('Fragment')
            
            # Check if each tag is imported or defined in file
            missing = []
            for tag in sorted(jsx_tags):
                # Check if tag exists in import statement or function/const definition
                if not re.search(r'\b' + tag + r'\b', content[:content.find('export default') if 'export default' in content else len(content)]):
                    # double check if defined anywhere above usage
                    missing.append(tag)
            if missing:
                print(f"[{f}] Potential missing components/icons: {missing}")
