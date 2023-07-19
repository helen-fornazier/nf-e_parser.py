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
            'prod_qCom': 0,
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

# Função para listar todos os arquivos xml em um diretório e seus subdiretórios e escrever os dados extraídos no arquivo CSV
def list_xml_files_in_directory_and_write_to_csv(dir_path, csv_path):
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['tipo', 'ide_dhEmi', 'emit_CNPJ', 'emit_xNome', 'dest_CNPJ', 'dest_xNome', 'prod_xProd', 'prod_qCom', 'prod_uCom', 'arquivo']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

        writer.writeheader()

        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.xml'):
                    file_path = os.path.join(root, file)
                    print(f'Processando arquivo: {file_path}')
                    row = extract_data_from_xml(file_path)
                    writer.writerow(row)


if __name__ == '__main__':
    # Definindo argumentos do script
    parser = argparse.ArgumentParser(description='Processa arquivos XML e extrai dados para um arquivo CSV.')
    parser.add_argument('dir_path', type=str, help='Caminho para o diretório contendo arquivos XML')
    parser.add_argument('csv_path', type=str, help='Caminho para o arquivo CSV onde os dados extraídos serão salvos')

    args = parser.parse_args()

    list_xml_files_in_directory_and_write_to_csv(args.dir_path, args.csv_path)
