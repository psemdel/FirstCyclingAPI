from ..endpoints import ParsedEndpoint
from ..parser import parse_table
import pandas as pd

class RaceEndpoint(ParsedEndpoint):
	"""
	Race page response. Extends Endpoint.

	Attributes
	----------
	header_details : dict
		Details from page header, including race name and external links.
	editions : list[int]
		A lsit of the years in which editions of the race took place.
	"""

	def _parse_soup(self):
		self._get_header_details()
		self._get_editions()

	def _get_header_details(self):
		self.header_details = {}
		self.header_details['name'] = self.soup.h1.text.rsplit(' - ', maxsplit=1)[0] # Get race name, excluding year
		self.header_details['links'] = {a.img['src'].rsplit('/', maxsplit=1)[1][:-7]: a['href'] for a in self.soup.h1.parent.find_all('a')}
		if 'www' in self.header_details['links']:
			self.header_details['links']['website'] = self.header_details['links'].pop('www')

	def _get_editions(self):
		self.editions = [int(o['value']) for o in self.soup.find('select', {'name': 'y'}).find_all('option') if o['value']]


class RaceVictoryTable(RaceEndpoint):
	"""
	Race victory table response. Extends RaceEndpoint.

	Attributes
	----------
	table : pd.DataFrame
		Victory table for race.
	"""

	def _parse_soup(self):
		super()._parse_soup()
		self._get_victory_table()
		

	def _get_victory_table(self):
		victory_table = self.soup.find('table', {'class': 'tablesorter'})
		self.table = parse_table(victory_table)

class Standing():
    def __init__(self, results_table):
        self.results_table=results_table
        
class RaceStageVictories(RaceEndpoint):
	"""
	Race stage victory table response. Extends RaceEndpoint.

	Attributes
	----------
	table : pd.DataFrame
		Stage victory table for race.
	"""

	def _parse_soup(self):
		super()._parse_soup()
		self._get_stage_victory_table()

	def _get_stage_victory_table(self):
		victory_table = self.soup.find('table', {'class': 'test tablesorter'}) # TODO test
		self.table = parse_table(victory_table)

class Standing():
    def __init__(self, results_table):
        self.results_table=results_table
        
class RaceEditionResults(RaceEndpoint):
	"""
	Race edition results response. Extends RaceEndpoint.

	Attributes
	----------
	results_table : pd.DataFrame
		Table containing the race results.
	standings : dict {str : pd.DataFrame}
		For stage races, maps classification names to a DataFrame with the appropriate standings after the stage.
	"""
	
	def _parse_soup(self):
		super()._parse_soup()
		self._get_results_table()
		self._get_sidebar_information()
        
	def _get_results_table(self):
		# Load all classification standings after stage
        # test if old race type or new race type:
        
		results_table = self.soup.find('table', {'class': 'sortTabell tablesorter'})
		if not results_table:
		    results_table = self.soup.find('table', {'class': 'sortTabell2 tablesorter'})
            
		if results_table: #old race type
		    self.results_table = parse_table(results_table)
    
		divs = self.soup.find_all('div', {'class': "tab-content"}) #includes also tab-content results
		self.standings= {div['id']: Standing(parse_table(div.table)) for div in divs}
        
		if not results_table:
		    self.results_table = self.standings[divs[0]['id']].results_table #first appearing is the result

	def _get_sidebar_information(self): # TODO
		return
    
class RaceEditionStartlist(RaceEndpoint): 
    def _parse_soup(self):
        super()._parse_soup()
        self._get_results_table()
        
    def _get_results_table(self):    
        tables = self.soup.find_all('table', {'class': 'tablesorter'})
        
        arr=[]
        
        for t in tables:
           sub_df=pd.read_html(str(t), decimal=',')[0]
           sub_df.columns=["BIB","Inv name"]
           sub_df["Inv name"]=sub_df["Inv name"].str.lower()
           sub_df["Inv name"]=sub_df["Inv name"].str.replace("[*]","",regex=False)
           sub_df["Inv name"]=sub_df["Inv name"].str.replace(" *","",regex=False)
           sub_df["Inv name"]=sub_df["Inv name"].str.replace("*","",regex=False)
           sub_df["Inv name"]=sub_df["Inv name"].str.replace("  "," " ,regex=False)

           arr.append(sub_df)
       
        bib_df =pd.concat(arr)
        self.bib_df = bib_df.set_index(bib_df["Inv name"])
