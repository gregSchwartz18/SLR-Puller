from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
from io import BytesIO
#from reportlab.pdfgen import canvas
from django.http import HttpResponse
import csv
import json
from django.urls import path
from django.template.loader import get_template
#from xhtml2pdf import pisa
from pathlib import Path

import io
import requests
from PyPDF2 import PdfReader, PdfWriter

import re
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

#import browser_cookie3
import shutil
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import pathlib
import glob
import os


def home(request):
	return render(request, 'home.html')

def scrape(request):
	if request.method == 'POST':
		citation = request.POST.get('citation')
		vol, page = citation.split(" U.S. ")

		URL = "https://heinonline.org/HOL/FCoption?terms={0}%20U.S.%20{1}&collection=journals&tabfrom=citation_tab&public=false&collection=&handle=hein.usreports/usrep410&id=185&men_hide=false&men_tab=citation_tab&kind=citation".format(vol, page)
		page = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
		soup = BeautifulSoup(page.content, "html.parser")
		results =soup.find_all("a")
		link = ""
		for r in results:
			if "HeinOnline (PDF version)" in r.text:
				link = "https://heinonline.org/HOL/"+r['href']
				break

		URL = link
		headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36", 
				"Accept":"text/html,application/xhtml+xml,application/xml; q=0.9,image/webp,image/apng,*/*;q=0.8"}
		page = requests.get(URL, headers=headers)
		soup = BeautifulSoup(page.content, "html.parser")
		results =soup.find_all("a")

		context = {
			'url': ""
		}
		for r in results:
			if "Download PDF of This Section" in r.text:
				context['url'] = "https://heinonline.org/HOL/"+r['href']
				break


		request.session['download_link'] = context
		return render(request, 'result.html', context)
	else:
		return render(request, 'home.html')

def download_file(request):
	if 'download_link' in request.session:
		download_link = request.session['download_link']['url']
		headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36", 
				"Accept":"text/html,application/xhtml+xml,application/xml; q=0.9,image/webp,image/apng,*/*;q=0.8"}
		response = requests.get(download_link, headers=headers)
		current_file_path = str(pathlib.Path(__file__).parent.resolve())

		chrome_options = webdriver.ChromeOptions()
		chrome_options.add_argument('--no-sandbox')
		chrome_options.add_argument('--disable-dev-shm-usage')
		chrome_options.add_argument("--headless")
		chrome_options.add_argument("--disable-gpu")
		chrome_options.add_experimental_option('prefs', {
			'download.default_directory': current_file_path,
			'download.prompt_for_download': False,
			'download.directory_upgrade': True,
			'safebrowsing.enabled': True
		})

		# Create a Chrome WebDriver instance
		driver = webdriver.Chrome(options=chrome_options)

		# Navigate to the specified URL
		driver.get(download_link)

		time.sleep(3)  # Wait for 10 seconds

		file_type = '.pdf'
		files = glob.glob(current_file_path + "/*" + file_type)
		max_file = max(files, key=os.path.getctime)
		os.rename(max_file, current_file_path+'/temp.pdf')

		infile = PdfReader(current_file_path+'/temp.pdf', 'rb')
		output = PdfWriter()

		for i in range(len(infile.pages)):
			if i != 0:
				p = infile.pages[i] 
				output.add_page(p)

		# Create an in-memory file-like object to hold the PDF content
		pdf_content = io.BytesIO()
		output.write(pdf_content)
		pdf_content.seek(0)

		os.remove(current_file_path+'/temp.pdf')

		# Return the captured content as a PDF response
		response = HttpResponse(pdf_content.read(), content_type='application/pdf')
		response['Content-Disposition'] = 'attachment; filename="SP-###.pdf"'
		return response



		'''s = requests.Session()
		headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36", 
				"Accept":"text/html,application/xhtml+xml,application/xml; q=0.9,image/webp,image/apng,*/*;q=0.8"}
		response = s.get(url=download_link, headers=headers, timeout=120)
		url_pattern = re.compile("window.location='(?P<url>.*)';")
		html = response.text
		match_result = url_pattern.search(html)
		url = match_result.group('url')
		content_response = s.get(url)
		file_content = content_response.content
		with open('/tmp/file.pdf', 'wb') as f:
		    f.write(file_content)


		headers = {'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'}

		response = requests.get(url=download_link, headers=headers, timeout=120)
		on_fly_mem_obj = io.BytesIO(response.content)
		pdf_file = PdfReader(on_fly_mem_obj)
		filename = "test"

		response = HttpResponse(file_content, headers={
			'Content-Type': 'application/pdf',
			'Content-Disposition': f'attachment; filename="{filename}"'
		})

		return response'''

	else:
		return render(request, 'home.html')




