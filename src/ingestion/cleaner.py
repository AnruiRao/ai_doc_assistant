import re

def clean_text(raw: str) -> str:
    if not raw:
        return ""
    
    text = raw.strip()

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.replace('　', ' ')

    text = re.sub(r"""[^\u4e00-\u9fff\w\s，。、；：？！""''（）【】《》——…·～,.!?;:'"()\[\]{}\-#@$%&*+=/<>~`|\\]""", '', text)

    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()

    