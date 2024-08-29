import csv
import sys
import requests
import pytesseract
from urllib.parse import quote
from pdf2image import convert_from_path
from PIL import Image
from unidecode import unidecode
from PyPDF2 import PdfReader

class AdresseHandler:
    def __init__(self, adresse):
        self.adresse = adresse
        self.latitude = None
        self.longitude = None
        self.latlon = None

    def convertir_en_diminutif(self):
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
            if key in self.adresse:
                self.adresse = self.adresse.replace(key, value)
        return self.adresse

    def fetch_latlon(self):
        print(f"Recherche de l'adresse: {self.adresse}")
        adresse = self.convertir_en_diminutif()
        response = requests.get(f'https://api-adresse.data.gouv.fr/search/?q={adresse}&autocomplete=1&limit=10').json()
        score = response['features'][0]['properties']['score']
        if score < 0.6:
            print(f"Adresse non trouvée pour : {self.adresse}")
            return None
        self.latitude = response['features'][0]['geometry']['coordinates'][1]
        self.longitude = response['features'][0]['geometry']['coordinates'][0]
        self.latlon = f'{self.longitude},{self.latitude}'
        return self.latlon


class PDFHandler:
    def __init__(self, latlon):
        self.latlon = latlon
        self.pdf_path = None

    def download_pdf(self):
        latlon_encoded = quote(self.latlon)
        response = requests.get(f"https://georisques.gouv.fr/api/v1/rapport_pdf?latlon={latlon_encoded}")
        self.pdf_path = f"rapport_{self.latlon}.pdf"
        with open(self.pdf_path, "wb") as f:
            f.write(response.content)
        return self.pdf_path

    def extract_page(self, page_number):
        reader = PdfReader(self.pdf_path)
        page = reader.pages[page_number]
        return page


class OCRProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def process_pdf(self, page_number):
        pages = convert_from_path(self.pdf_path, 300)
        image_path = f'{self.pdf_path}.png'
        pages[page_number].save(image_path, 'PNG')
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='fra')
        return self.clean_text(text)

    @staticmethod
    def clean_text(text):
        start_marker = "Adresse recherchée"
        end_marker = "Risques naturels identifiés"

        lines = text.split('\n')
        start_index = -1
        end_index = -1

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


class DataExtractor:
    @staticmethod
    def find_row(text, row_number):
        lines = text.split('\n')
        if row_number <= len(lines):
            return lines[row_number - 1]
        else:
            return None

    @staticmethod
    def extract_data(text):
        data = {}
        data['inondations'] = {
            'mon_adresse': DataExtractor.find_row(text, 22).split(' ')[0],
            'ma_commune': DataExtractor.find_row(text, 22).split(' ')[1]
        }
        data['seisme'] = {
            'mon_adresse': DataExtractor.find_row(text, 24).split(' ')[0],
            'ma_commune': DataExtractor.find_row(text, 24).split(' ')[1]
        }
        data['mouvement_de_sol'] = {
            'mon_adresse': DataExtractor.find_row(text, 26).split(' ')[0],
            'ma_commune': DataExtractor.find_row(text, 26).split(' ')[1]
        }
        data['retrait_gonflement'] = {
            'mon_adresse': DataExtractor.find_row(text, 28).split(' ')[1],
            'ma_commune': DataExtractor.find_row(text, 28).split(' ')[2]
        }
        data['feu_de_foret'] = {
            'mon_adresse': DataExtractor.find_row(text, 8),
            'ma_commune': DataExtractor.find_row(text, 15)
        }
        data['radon'] = {
            'mon_adresse': DataExtractor.find_row(text, 11),
            'ma_commune': DataExtractor.find_row(text, 19)
        }
        data['canalisations_de_transport_de_matiere_dangereuse'] = {
            'mon_adresse': DataExtractor.find_row(text, 42),
            'ma_commune': DataExtractor.find_row(text, 53)
        }
        data['polution_des_sols'] = {
            'mon_adresse': DataExtractor.find_row(text, 45),
            'ma_commune': DataExtractor.find_row(text, 57)
        }
        data['rupture_de_barrage'] = {
            'mon_adresse': DataExtractor.find_row(text, 49),
            'ma_commune': DataExtractor.find_row(text, 61)
        }
        print(data)
        return data


class CSVWriter:
    def __init__(self, filename):
        self.filename = filename
        self.headers = ['Adresse', 'Inondations (Mon Adresse)', 'Inondations (Ma Commune)', 'Seisme (Mon Adresse)', 'Seisme (Ma Commune)',
                        'Mouvement de Sol (Mon Adresse)', 'Mouvement de Sol (Ma Commune)', 'Retrait Gonflement (Mon Adresse)',
                        'Retrait Gonflement (Ma Commune)', 'Feu de Forêt (Mon Adresse)', 'Feu de Forêt (Ma Commune)',
                        'Radon (Mon Adresse)', 'Radon (Ma Commune)', 'Canalisations de Transport de Matière Dangereuse (Mon Adresse)',
                        'Canalisations de Transport de Matière Dangereuse (Ma Commune)', 'Pollution des Sols (Mon Adresse)',
                        'Pollution des Sols (Ma Commune)', 'Rupture de Barrage (Mon Adresse)', 'Rupture de Barrage (Ma Commune)']

        with open(self.filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

    def append_data(self, row, data):
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                row,
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


class MainApp:
    def __init__(self, input_file):
        self.input_file = input_file

    def run(self):
        csv_writer = CSVWriter('output.csv')
        with open(self.input_file, 'r') as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                adresse_handler = AdresseHandler(row[0])
                latlon = adresse_handler.fetch_latlon()
                if latlon:
                    pdf_handler = PDFHandler(latlon)
                    pdf_path = pdf_handler.download_pdf()
                    ocr_processor = OCRProcessor(pdf_path)
                    text = ocr_processor.process_pdf(1)
                    data = DataExtractor.extract_data(text)
                    csv_writer.append_data(row[0], data)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    app = MainApp(input_file)
    app.run()
