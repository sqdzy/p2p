from bs4 import BeautifulSoup as bs
import requests
from django.db import transaction
from .models import Currency, ExchangeRate
import datetime

class Rates:
    def __init__(self):
        self.__cbrf_url = "https://www.cbr.ru/scripts/XML_daily.asp"
    def get_rate(self, charcode:str):
        try:
            xml_content = requests.get(self.__cbrf_url).content
            soup = bs(xml_content, 'xml')
            valute = soup.find('CharCode', string=charcode).find_parent('Valute')
            vunitrate = valute.find('VunitRate').text
            return round(float(vunitrate.replace(",", ".").strip()), 3)
        except:
            return "Сервера центробанка РФ не доступны"

    @transaction.atomic
    def get_rates(self):
        try:
            xml_content = requests.get(self.__cbrf_url).content
            soup = bs(xml_content, 'xml')
            valutes = soup.find_all('Valute')
            today = datetime.date.today()
            for valute in valutes:
                vunitrate = round(float(valute.find('VunitRate').text.replace(",", ".").strip()), 3)
                charcode = valute.find('CharCode').text
                name = valute.find('Name').text
                cur_code, created = Currency.objects.get_or_create(
                    currency_code=charcode,
                    defaults={'currency_name': name},
                )
                ExchangeRate.objects.update_or_create(
                    currency_code=cur_code,
                    effective_date=today,
                    defaults={'rate': vunitrate},
                )
            return f"Данные актуальны на {today}"
        except:
            return "Сервера центробанка РФ не доступны"



