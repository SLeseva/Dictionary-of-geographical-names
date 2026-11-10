import argparse
import re
import sys
import os

def read_templates_db(filename):
    templates = {}
    if not os.path.exists(filename):
        print(f"Грешка: Файлът с шаблони '{filename}' не съществува!", file=sys.stderr)
        sys.exit(1)
        
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, content = line.split("=", 1)
            templates[name.strip()] = content.strip()
    return templates


TOKEN_RE = re.compile(r"(<1>|<2>|<L\d*>|<R\d*>|<S>)")

def apply_expression(expr_body, w1, w2, template_name=""):
    """Изпълнява израз със замествания и команди за курсор.
    <1>, <2>  - първата и втората дума
    <Ln>      - курсорът n символа наляво (<L> = 1)
    <Rn>      - курсорът n символа надясно (<R> = 1)
    <S>       - изтрива символа вдясно от курсора
    Курсорът започва в края; обикновеният текст се вмъква при курсора."""
    text = ""
    cur = 0
    for tok in TOKEN_RE.split(expr_body):
        if not tok:
            continue
        if tok == "<1>":
            text = text[:cur] + w1 + text[cur:]
            cur += len(w1)
        elif tok == "<2>":
            text = text[:cur] + w2 + text[cur:]
            cur += len(w2)
        elif tok == "<S>":
            text = text[:cur] + text[cur + 1:]
        elif re.fullmatch(r"<L\d*>", tok):
            n = int(tok[2:-1] or 1)
            cur = max(0, cur - n)
        elif re.fullmatch(r"<R\d*>", tok):
            n = int(tok[2:-1] or 1)
            cur = min(len(text), cur + n)
        else:
            text = text[:cur] + tok + text[cur:]
            cur += len(tok)
    return text

def generate_forms_for_line(line, templates_db):
    line = line.strip()
    if not line or "," not in line:
        return []
    
    # Входен формат: айтоски проход,NHMS3-0_A_NCM
    lemma, template_name = line.rsplit(",", 1)
    lemma = lemma.strip()
    template_name = template_name.strip()
    
    if template_name not in templates_db:
        print(f"Грешка: Шаблонът '{template_name}' за съставната дума '{lemma}' не е дефиниран!", file=sys.stderr)
        return []
    
    template_content = templates_db[template_name]
    expressions = [expr.strip() for expr in template_content.split("+")]
    
    # Правилно разделяме съставната лема на две текстови думи
    lemma_parts = lemma.split(maxsplit=1)
    if len(lemma_parts) < 2:
        w1 = lemma
        w2 = ""
    else:
        w1 = lemma_parts[0]
        w2 = lemma_parts[1]
        
    results = []
    for expression in expressions:
        if "/" not in expression:
            continue
        expr_body, label = expression.rsplit("/", 1)
        
        # Заместване на променливите с чист текст (str)
        form = apply_expression(expr_body.strip(), w1, w2, template_name)
        form = " ".join(form.split())
        if re.search(r"<[^>]*>", form):
            print(f"Предупреждение: останала е непознатa команда във '{form}' "
                  f"(шаблон {template_name})", file=sys.stderr)
        
        # Краен формат: словоформа,лема.ТИП/етикет
        results.append(f"{form},{lemma}.{template_name}/{label}")
        
    return results

def main():
    parser = argparse.ArgumentParser(description="Поправен генератор на съставни форми.")
    parser.add_argument("templates")
    parser.add_argument("input")
    parser.add_argument("output")
    
    args = parser.parse_args()
    templates_db = read_templates_db(args.templates)
    
    output_lines = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            forms = generate_forms_for_line(line, templates_db)
            output_lines.extend(forms)
            
    with open(args.output, "w", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")
            
    print(f"Готово! Успешно генерирани съставни форми: {len(output_lines)}")

if __name__ == "__main__":
    main()
