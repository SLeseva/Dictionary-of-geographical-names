import argparse
import sys
import re
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

def apply_operations(lemma, operations):
    """Изпълнява команди за курсор върху лемата. Курсорът започва в края.
    <Ln> - курсорът n символа наляво (<L> = <L1>)
    <Rn> - курсорът n символа надясно (<R> = <R1>)
    <Sn> - изтрива n символа вдясно от курсора (<S> = <S1>)
    Напр. южен -> южн: <L2><S><R1>  (наляво 2, трий 'е', надясно 1)"""
    result = lemma
    position = len(result)
    for operation in operations:
        kind = operation[0]
        n = int(operation[1:] or 1)
        if kind == "L":
            position = max(0, position - n)
        elif kind == "R":
            position = min(len(result), position + n)
        elif kind == "S":
            result = result[:position] + result[position + n:]
    return result

def generate_forms_for_line(line, templates_db):
    line = line.strip()
    if not line or "," not in line:
        return []
    
    # Входен формат: настоя,V_PE_IT_S2_04
    lemma, template_name = line.rsplit(",", 1)
    lemma = lemma.strip()
    template_name = template_name.strip()
    
    if template_name not in templates_db:
        print(f"Грешка: Шаблонът '{template_name}' за думата '{lemma}' не е дефиниран във външния файл!", file=sys.stderr)
        return []
    
    template_content = templates_db[template_name]
    expressions = [expr.strip() for expr in template_content.split("+")]
    
    results = []
    for expression in expressions:
        if "/" not in expression:
            continue
        expr_body, label = expression.rsplit("/", 1)
        
        # Извличане и прилагане на операциите (L1, S)
        operations = re.findall(r"<([LRS]\d*)>", expr_body)
        form = apply_operations(lemma, operations)
        
        # Добавяне на окончанието
        suffix = re.sub(r"<(?:1|[LRS]\d*)>", "", expr_body)
        form += suffix
        
        # Краен формат: словоформа,лема.ТИП/етикет
        results.append(f"{form},{lemma}.{template_name}/{label}")
        
    return results

def main():
    parser = argparse.ArgumentParser(description="Генератор на прости форми по запетая.")
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
            
    print(f"Готово! Успешно генерирани прости форми: {len(output_lines)}")

if __name__ == "__main__":
    main()
