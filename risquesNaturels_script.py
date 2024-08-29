import csv
import sys
import requests
import pytesseract
from urllib.parse import quote
from pdf2image import convert_from_path
from PIL import Image
from PyPDF2 import PdfReader

def convertir_en_diminutif(chaine):
    """
    Convertit les longues formes latines en diminutifs pour simplifier la recherche d'adresses.
    """
    diminutifs = {
        " bis": "b", " ter": "t", " quater": "q", " quinquies": "qn", " sexies": "s", " septies": "sp", " octies": "o", " nonies": "n", " decies": "d",
        " undecies": "u", " duodecies": "du", " terdecies": "td", " quaterdecies": "qd", " quindecies": "qd", " sexdecies": "sd", " septdecies": "spd",
        " octodecies": "od", " novodecies": "nd", " vicies": "v", " unvicies": "uv", " duovicies": "dv", " tervicies": "tv", " quatervicies": "qv",
        " quinvicies": "qv", " sexvicies": "sv", " septvicies": "spv", " octovicies": "ov", " novovicies": "nv", " tricies": "t", " untricies": "ut",
        " duotricies": "dt", " tertricies": "tt", " quatertricies": "qt", " quintricies": "qt", " sextricies": "st", " septtricies": "spt",
        " octotricies": "ot", " novotricies": "nt", " quadragies": "q", " unquadragies": "uq", " duoquadragies": "dq", " terquadragies": "tq",
        " quaterquadragies": "qq", " quinquadragies": "qq", " sexquadragies": "sq", " septquadragies": "spq", " octoquadragies": "oq",
        " novoquadragies": "nq", " quinquagies": "q", " unquinquagies": "uq", " duoquinquagies": "dq", " terquinquagies": "tq", " quaterquinquagies": "qq",
        " quinquinquagies": "qq", " sexquinquagies": "sq", " septquinquagies": "spq", " octoquinquagies": "oq", " novoquinquagies": "nq", " sexagies": "s",
        " unsexagies": "us", " duosexagies": "ds", " tersexagies": "ts", " quatersexagies": "qs", " quinsexagies": "qs", " sexsexagies": "ss",
        " septsexagies": "sps", " octosexagies": "os", " novosexagies": "ns"
    }
    for key, value in diminutifs.items():
        if key in chaine:
            chaine = chaine.replace(key, value)
    return chaine

def latlon(adresse):
    """
    Obtient la latitude et la longitude d'une adresse en utilisant une API de géocodage.
    
    :param adresse: Liste contenant l'adresse à rechercher.
    :return: Chaîne contenant la latitude et la longitude séparées par une virgule.
    """
    adresse_str = adresse[0]
    print(f"Recherche de l'adresse: {adresse_str}")
    adresse = adresse_str.replace(',', ' ')
    response = requests.get(f'https://api-adresse.data.gouv.fr/search/?q={convertir_en_diminutif(adresse)}&autocomplete=1&limit=10').json()
    score = response['features'][0]['properties']['score']
    if score < 0.6:
        print(f"Adresse non trouvée pour : {adresse_str}")
        return None
    latitude = response['features'][0]['geometry']['coordinates'][1]
    longitude = response['features'][0]['geometry']['coordinates'][0]
    latlon = f'{longitude},{latitude}'
    return latlon

def pdf(latitudelongitude):
    """
    Télécharge un rapport PDF basé sur la latitude et la longitude fournies.

    :param latitudelongitude: Chaîne contenant la latitude et la longitude.
    :return: La page PDF demandée et le chemin vers le fichier PDF.
    """
    latlon_encoded = quote(latitudelongitude)
    response = requests.get(f"https://georisques.gouv.fr/api/v1/rapport_pdf?latlon={latlon_encoded}")
    pdf_path = f"rapport_{latitudelongitude}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(response.content)
    reader = PdfReader(pdf_path)
    page = reader.pages[1]
    return page, pdf_path

def process_pdf(pdf_path, page_number):
    """
    Extrait le texte d'une page PDF spécifiée en utilisant OCR (Reconnaissance Optique de Caractères).
    
    :param pdf_path: Chemin vers le fichier PDF.
    :param page_number: Numéro de la page à traiter.
    :return: Texte nettoyé extrait de la page.
    """
    pages = convert_from_path(pdf_path, 300)
    image_path = f'{pdf_path}.png'
    pages[page_number].save(image_path, 'PNG')
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang='fra')
    # pour print le text OCR ==> print(text)
    
    # Définir les marqueurs de début et de fin pour le texte à extraire
    start_marker = "Adresse recherchée"
    end_marker = "Risques naturels identifiés"

    lines = text.split('\n')
    start_index = -1
    end_index = -1

    # Trouver les indices de début et de fin du texte à conserver
    for i, line in enumerate(lines):
        if start_marker in line:
            start_index = i
        if end_marker in line and start_index != -1:
            end_index = i
            break

    if start_index != -1 and end_index != -1:
        del lines[start_index:end_index + 1]

    cleaned_text = '\n'.join(lines)
    print(cleaned_text)
    return cleaned_text

def findRow(text, rowNumber):
    """
    Trouve une ligne spécifique dans le texte basé sur le numéro de la ligne.
    
    :param text: Texte à analyser.
    :param rowNumber: Numéro de la ligne à extraire.
    :return: Contenu de la ligne spécifiée ou None si le numéro est hors limites.
    """
    lines = text.split('\n')
    if rowNumber <= len(lines):
        return lines[rowNumber - 1]
    else:
        return None

def extract_data(text):
    """
    Extrait les données spécifiques à partir du texte nettoyé.

    :param text: Texte nettoyé extrait du PDF.
    :return: Dictionnaire contenant les données extraites pour chaque type de risque.
    """
    data = {}
    data['inondations'] = {
        'mon_adresse': findRow(text, 22).split(' ')[0],
        'ma_commune': findRow(text, 22).split(' ')[1]
    }
    data['seisme'] = {
        'mon_adresse': findRow(text, 24).split(' ')[0],
        'ma_commune': findRow(text, 24).split(' ')[1]
    }
    data['mouvement_de_sol'] = {
        'mon_adresse': findRow(text, 26).split(' ')[0],
        'ma_commune': findRow(text, 26).split(' ')[1]
    }
    data['retrait_gonflement'] = {
        'mon_adresse': findRow(text, 28).split(' ')[1],
        'ma_commune': findRow(text, 28).split(' ')[2]
    }
    data['feu_de_foret'] = {
        'mon_adresse': findRow(text, 8),
        'ma_commune': findRow(text, 15)
    }
    data['radon'] = {
        'mon_adresse': findRow(text, 11),
        'ma_commune': findRow(text, 19)
    }
    data['canalisations_de_transport_de_matiere_dangereuse'] = {
        'mon_adresse': findRow(text, 42),
        'ma_commune': findRow(text, 53)
    }
    data['polution_des_sols'] = {
        'mon_adresse': findRow(text, 45),
        'ma_commune': findRow(text, 57)
    }
    data['rupture_de_barrage'] = {
        'mon_adresse': findRow(text, 49),
        'ma_commune': findRow(text, 61)
    }
    print(data)
    return data

def main(allAddress):
    """
    Fonction principale pour traiter les adresses et enregistrer les résultats dans un fichier CSV.

    :param allAddress: Chemin vers le fichier CSV contenant les adresses.
    """
    headers = ['Adresse', 'Inondations (Mon Adresse)', 'Inondations (Ma Commune)', 'Seisme (Mon Adresse)', 'Seisme (Ma Commune)',
               'Mouvement de Sol (Mon Adresse)', 'Mouvement de Sol (Ma Commune)', 'Retrait Gonflement (Mon Adresse)',
               'Retrait Gonflement (Ma Commune)', 'Feu de Forêt (Mon Adresse)', 'Feu de Forêt (Ma Commune)',
               'Radon (Mon Adresse)', 'Radon (Ma Commune)', 'Canalisations de Transport de Matière Dangereuse (Mon Adresse)',
               'Canalisations de Transport de Matière Dangereuse (Ma Commune)', 'Pollution des Sols (Mon Adresse)',
               'Pollution des Sols (Ma Commune)', 'Rupture de Barrage (Mon Adresse)', 'Rupture de Barrage (Ma Commune)']

    # Ouvrir le fichier CSV pour écrire les en-têtes
    with open('output.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

    # Lire le fichier d'adresses et traiter chaque adresse
    with open(allAddress, 'r') as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            latitudelongitude = latlon(row)
            if latitudelongitude:
                page, pdf_path = pdf(latitudelongitude)
                text = process_pdf(pdf_path, 1)
                data = extract_data(text)

                # Ouvrir le fichier CSV en mode ajout et écrire les données
                with open('output.csv', 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        row[0],
                        data['inondations']['mon_adresse'], data['inondations']['ma_commune'],
                        data['seisme']['mon_adresse'], data['seisme']['ma_commune'],
                        data['mouvement_de_sol']['mon_adresse'], data['mouvement_de_sol']['ma_commune'],
                        data['retrait_gonflement']['mon_adresse'], data['retrait_gonflement']['ma_commune'],
                        data['feu_de_foret']['mon_adresse'], data['feu_de_foret']['ma_commune'],
                        data['radon']['mon_adresse'], data['radon']['ma_commune'],
                        data['canalisations_de_transport_de_matiere_dangereuse']['mon_adresse'],
                        data['canalisations_de_transport_de_matiere_dangereuse']['ma_commune'],
                        data['polution_des_sols']['mon_adresse'], data['polution_des_sols']['ma_commune'],
                        data['rupture_de_barrage']['mon_adresse'], data['rupture_de_barrage']['ma_commune']
                    ])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_input_file>")
        sys.exit(1)

    allAddress = sys.argv[1]
    main(allAddress)
