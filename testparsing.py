from pyparsing import *
import xml.etree.ElementTree as ET
import sys

# Определение идентификаторов и чисел
identifier = Combine(Word('_QWERTYUIOPLKJHGFDSAZXCVBNM') + ZeroOrMore(Word('_'+alphanums)))
number = Word('0123456789')


array_pointer = Forward()
dictionary_pointer = Forward()

# Определение конструкции массива
def make_array_pointer():
    return Suppress('#') + Suppress('(') + Group(delimitedList((number | identifier | array_pointer | dictionary_pointer))
                                                 ).setParseAction(lambda t: ("array", *t[0])) + Suppress(')')
# Определение конструкции словаря
def make_dictionary_pointer():
    return Suppress('{') + Dict(OneOrMore(
        Group(identifier + Suppress('->') + (identifier | number | array_pointer | dictionary_pointer) + Suppress('.'))
        )).setParseAction(lambda t: ("dict",{k: v for k, v in t.items()} )) + Suppress('}')


array_pointer <<= make_array_pointer()
dictionary_pointer <<= make_dictionary_pointer()

# Операции
add_op = Literal("+")
sub_op = Literal("-")
mod_op = Literal("mod")

op_expression = Group(Suppress("![")+(add_op | sub_op | mod_op) + (identifier | number) + (identifier | number) + Suppress("]")).setParseAction(lambda t: ("exp", *t[0]))

# Присваивание константы
const_assign = Group(identifier + Suppress('<-') + (op_expression | number))

# Главная структура программы
program = OneOrMore(const_assign | array_pointer | dictionary_pointer) + Suppress('EOF')



constants={}
# Вычисление константы
def calculate_exp(exp):
    if(exp[2].isdigit()):
        a=int(exp[2])
    else:
        if(exp[2] in constants):
             a=int(constants[exp[2]])
        else:
            return "Error: not found "+exp[2]

    if(exp[3].isdigit()):
        b=int(exp[3])
    else:
        if(exp[3] in constants):
             b=int(constants[exp[3]])
        else:
            return "Error: not found "+exp[3]
        
    if(exp[1]=="+"):
        return a+b
    elif (exp[1]=="-"):
        return a-b
    else:
        return a%b
# Перевод в xml
def to_xml(result):
    root = ET.Element("Doc_xml")

    def add_element(parent, item):
        if item[0] == "dict":
            dict_elem = ET.SubElement(parent, "Dictionary")
            for k, v in item[1].items():
                entry_elem = ET.SubElement(dict_elem, "Entry")
                ET.SubElement(entry_elem, "Key").text=k
                log = add_element(entry_elem, v)
                if("Error") in log:
                    return log
        elif item[0] == "array":
            array_elem = ET.SubElement(parent, "Array")
            for value in item[1:]:
                log = add_element(array_elem, value)
                if("Error") in log:
                    return log
        elif not(isinstance(item, str)):
            assign_elem = ET.SubElement(parent, "const", name=item[0])
            if (item[1][0]=="exp"):
                value = str(calculate_exp(item[1]))
                assign_elem.text = value
                constants[item[0]] = value
                if ("Error" in value):
                    return "Error: not found "+item[1]
            else:
                assign_elem.text = str(item[1])
                constants[item[0]]=item[1]
        else:
            if(item.isdigit()):
                ET.SubElement(parent, "Value").text = item
            else:
                if(item in constants):
                    ET.SubElement(parent, "Value").text = constants[item]
                else:
                    return "Error: not found "+item
        return ""
            

    for item in result:
        log = add_element(root, item)
        if("Error" in log):
            return log

    return ET.tostring(root, encoding='unicode')


try:
    inputfile = open(sys.argv[1])
    data=""
    for line in inputfile:
        data+=line
    data+="EOF"
    result = program.parseString(data)
    xml_result = to_xml(result)
    if("Error" in xml_result):
        print(xml_result)
    else:
        inputfile.close()
        outputfile = open(sys.argv[2], 'w')
        outputfile.write(xml_result)
    
except ParseException as pe:
    print(f"Ошибка парсинга: {pe}")
    print(f"Ошибка на строке: {pe.line} (номер строки: {pe.lineno})")
except Exception as e:
    print("Произошла неожиданная ошибка:", e)

