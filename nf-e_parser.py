import csv
import os
import xml.etree.ElementTree as ET
import argparse

def extract_data_from_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Utilizando os namespaces
    namespace_NFe = {'ns': 'http://www.portalfiscal.inf.br/nfe'}

    # Verificando o tipo do arquivo XML
    if root.find(".//ns:NFe", namespace_NFe) is not None:
        # Se o arquivo XML for NFe, extrai os dados como antes
        tipo = "NFe"
        emit_CNPJ = root.find(".//ns:emit/ns:CNPJ", namespace_NFe)
        emit_xNome = root.find(".//ns:emit/ns:xNome", namespace_NFe)
        dest_CNPJ = root.find(".//ns:dest/ns:CNPJ", namespace_NFe)
        dest_xNome = root.find(".//ns:dest/ns:xNome", namespace_NFe)
        prod_xProd = root.find(".//ns:prod/ns:xProd", namespace_NFe)
        prod_uCom = root.find(".//ns:prod/ns:uCom", namespace_NFe)
        prod_qCom = root.find(".//ns:prod/ns:qCom", namespace_NFe)
        ide_dhEmi = root.find(".//ns:ide/ns:dhEmi", namespace_NFe)
    elif root.tag == 'CFe':
        # Se o arquivo XML for CFe, extrai os dados de acordo com o novo formato
        tipo = "CFe"
        emit_CNPJ = root.find("./infCFe/emit/CNPJ")
        emit_xNome = root.find("./infCFe/emit/xNome")
        dest_CNPJ = root.find("./infCFe/dest/CNPJ") # CFe não possui tag dest:CNPJ, o valor vai ser None
        dest_xNome = root.find("./infCFe/dest/xNome") # CFe não possui tag dest:xNome, o valor vai ser None
        prod_xProd = root.find("./infCFe/det/prod/xProd")
        prod_uCom = root.find("./infCFe/det/prod/uCom")
        prod_qCom = root.find("./infCFe/det/prod/qCom")
        ide_dhEmi = root.find("./infCFe/ide/dEmi")
    else:
        return {
            'tipo': 'desconhecido',
            'emit_CNPJ': "",
            'emit_xNome': "",
            'dest_CNPJ': "",
            'dest_xNome': "",
            'prod_xProd': "",
            'prod_uCom': "",
            'prod_qCom': "",
            'ide_dhEmi': "",
            'arquivo': file_path,
        }

    # Retorna os valores como um dicionário
    return {
        'tipo': tipo,
        'emit_CNPJ': emit_CNPJ.text if emit_CNPJ is not None else "",
        'emit_xNome': emit_xNome.text if emit_xNome is not None else "",
        'dest_CNPJ': dest_CNPJ.text if dest_CNPJ is not None else "",
        'dest_xNome': dest_xNome.text if dest_xNome is not None else "",
        'prod_xProd': prod_xProd.text if prod_xProd is not None else "",
        'prod_uCom': prod_uCom.text if prod_uCom is not None else "",
        'prod_qCom': prod_qCom.text.replace(".", ",") if prod_qCom is not None else "",
        'ide_dhEmi': ide_dhEmi.text if ide_dhEmi is not None else "",
        'arquivo': file_path,
    }

def contains_any_substring(var, substrings):
    var = var.lower()
    return any(sub in var for sub in substrings)

# CNPJ 22659620000170	SUCATAS BERTASSO LTDA. ME.
# CNPJ 27051773000234	AMBIENTAL ABELARDI LTDA
# CNPJ 68108232000100	COMERCIO DE SUCATAS ABELARDI LTDA --------> NAO USAR

def classify_entrada_saida(row):
    entrada_cnpj = ["22659620000170", "27051773000234", "68108232000100"]
    if row['emit_CNPJ'] in entrada_cnpj:
        return 'saida'
    elif row['emit_CNPJ']:
        return 'entrada'

def classify_material(row):
    word_map = {
        "plastico": ["plast", "pet"],
        "vidro": ["vidro"],
        "papel/papelao": ["papel"],
        "metal": ["metal", "alum", "inox", "ferro", "aco"],
        "borracha": ["borracha", "pneu"],
        "madeira": ["madeira", "pallet"],
    }

    for material, words in word_map.items():
        if contains_any_substring(row['prod_xProd'], words):
            return material

    for material, words in word_map.items():
        if contains_any_substring(row['dest_xNome'], words):
            return material

def classify_elegibility(row):
    if not row["tipo"] or row["tipo"] == "desconhecido":
        return

    allowed_cnpj = ["22659620000170", "27051773000234"]
    material_eligble = ["plastico", "vidro", "papel/papelao", "metal"]
    if (row["material"] in material_eligble and row["entrada/saida"] == "saida"
        and contains_any_substring(row["prod_uCom"], ["kg", "ton"])
        and row["prod_qCom"] and float(row["prod_qCom"].replace(",", ".")) > 0
        and row["emit_CNPJ"] in allowed_cnpj
        and row["ide_dhEmi"][:4] in ["2020", "2021", "2022"]
        ):
        return "sim"
    elif (
        (row["material"] and row["material"] not in material_eligble)
        or row["entrada/saida"] == "entrada"
        or not contains_any_substring(row["prod_uCom"], ["kg", "ton"])
        or not row["prod_qCom"] or float(row["prod_qCom"].replace(",", ".")) <= 0
        or row["emit_CNPJ"] not in allowed_cnpj
        ):
        return "nao"


# Função para listar todos os arquivos xml em um diretório e seus subdiretórios e escrever os dados extraídos no arquivo CSV
def list_xml_files_in_directory_and_write_to_csv(dir_path, csv_path):
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['elegivel', 'tipo', 'ide_dhEmi', 'emit_CNPJ', 'emit_xNome', 'dest_CNPJ', 'dest_xNome', 'prod_xProd', 'prod_qCom', 'prod_uCom', 'entrada/saida', 'material', 'arquivo']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

        writer.writeheader()

        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.xml'):
                    file_path = os.path.join(root, file)
                    print(f'Processando arquivo: {file_path}')
                    row = extract_data_from_xml(file_path)
                    row['entrada/saida'] = classify_entrada_saida(row)
                    row['material'] = classify_material(row)
                    row['elegivel'] = classify_elegibility(row)
                    writer.writerow(row)


if __name__ == '__main__':
    # Definindo argumentos do script
    parser = argparse.ArgumentParser(description='Processa arquivos XML e extrai dados para um arquivo CSV.')
    parser.add_argument('dir_path', type=str, help='Caminho para o diretório contendo arquivos XML')
    parser.add_argument('csv_path', type=str, help='Caminho para o arquivo CSV onde os dados extraídos serão salvos')

    args = parser.parse_args()

    list_xml_files_in_directory_and_write_to_csv(args.dir_path, args.csv_path)
