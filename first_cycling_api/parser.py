"""
Parser
=========

Provides useful functions to parse API responses.
"""
import pandas as pd
import numbers
# Parsing dates ----

def parse_date(date_text):
	from dateutil.parser import parse as date_parse, ParserError

	try:
		return date_parse(date_text).date()
	except ParserError: # Result with uncertain date, use January/1st by default
		year, month, day = date_text.split('-')
		month = '01' if not int(month) else month
		day = '01' if not int(day) else day
		fixed_date = year + '-' + month + '-' + day
		return date_parse(fixed_date).date()

# Parsing links ----

def get_url_parameters(url): # Adapted from https://stackoverflow.com/questions/21584545/url-query-parameters-to-dict-python
	from urllib import parse as url_parse
	return dict(url_parse.parse_qsl(url_parse.urlsplit(url).query))

def rider_link_to_id(a):
	return int(get_url_parameters(a['href'])['r'])

def team_link_to_id(a):
	return int(get_url_parameters(a['href'])['l'])

def race_link_to_race_id(a):
	return int(get_url_parameters(a['href'])['r'])

def race_link_to_stage_num(a):
	return int(get_url_parameters(a['href'])['e'])

def link_to_twitter_handle(a):
	return a['href'].split('/')[3]

# Parsing icons ----

def get_img_name(img):
	return img['src'].split('/')[-1]

def img_to_country_code(img):
	""" Obtain three-letter country code, or 'UCI' or 'OL' from html img tag """
	return get_img_name(img).split('.')[0]

def img_to_profile(img):
	""" Return profile type for image """
	return profile_icon_map[get_img_name(img)]


# Parsing tables ----

def parse_table(table):
   	""" Convert HTML table from bs4 to pandas DataFrame. Return None if no data. """
   	# TODO for rider results, format dates nicely with hidden column we are throwing away
   	# Load pandas DataFrame from raw text only
   	out_df = pd.read_html(str(table), decimal=',')[0]

   	if out_df.iat[0, 0] == 'No data': # No data
   		return None
   
   	# Convert decimal points to thousands separator
   	# NOTE: Cannot use thousands='.' in pd.read_html because will ruin other columns (e.g. CAT for races)
   	thousands_cols = ['Points']
   	for col in thousands_cols:
   		if col in out_df:
   			out_df[col]=out_df[col].astype(str) 
   			for i in out_df.index:
  			    if out_df[col].loc[i].find("(")!=-1:
   			        out_df.loc[i,col]=out_df.loc[i, col][:out_df.loc[i,col].find("(")]
  			    if out_df[col].loc[i][-2:]==".0":
   			        out_df.loc[i, col]=out_df.loc[i, col].replace('.0', '') #to avoid that the .0 becomes 0
   			out_df[col] = out_df[col].str.replace('.', '', regex=False).astype(int)

   	# Parse soup to add information hidden in tags/links
   	if len([th.text for th in table.tr.find_all('th')])==0: #bug with youth, as a <tr> is missing
   		trs = table.find_all('tr')[0:]
   	else:
   		trs = table.find_all('tr')[1:]
       
   	headers = [th.text for th in table.thead.find_all('th')]
   
   	if 'Race.1' in out_df:
   		out_df = out_df.rename(columns={'Race': 'Race_Country', 'Race.1': 'Race'})
   		headers.insert(headers.index('Race'), 'Race_Country')
       
   	for col in out_df.columns: #problems with \nRider\n
   		if "Rider" in col:
   			out_df = out_df.rename(columns={col: 'Rider'})
   			break
   	for i, col in enumerate(headers): #problems with \nRider\n
   		if "Rider" in col:
   			headers[i]='Rider'
   			break
   
   	try:
   	    soup_df = pd.DataFrame([tr.find_all('td') for tr in trs], columns=headers)
   	except Exception as msg:
   		try: 
            #Empty time bug on the side of First Cycling
   			heads=headers[:-2]   
   			heads.append(headers[-1])
   			soup_df = pd.DataFrame([tr.find_all('td') for tr in trs], columns=heads)
   			out_df["Time"]=out_df[out_df.columns[-2]]
   		except:
   			print(msg)
   			print("A cause can be that the race is not completed yet")
   			return None

   	# Add information hidden in tags
   	for col, series in soup_df.items():
   		if col in ('Rider', 'Winner', 'Second', 'Third'):
   			if col =="Rider":
   			    out_df["Rider"]=out_df["Rider"].str.replace("[*]","",regex=False)
   			    out_df["Rider"]=out_df["Rider"].str.replace("*","",regex=False)
   			    out_df["Rider"]=out_df["Rider"].str.replace("  "," " ,regex=False)
   			    out_df["Inv name"]=out_df["Rider"].str.lower()
                   #reverse order of name
   			    for ii in range(len(series)):
   			        t=[s.text for s in series[ii].find_all("span")]
                       
   			        if len(t)>0:
   			            if t[0]=="": #flag
   			                last_name=t[1]
   			            else:
   			                last_name=t[0]
                        
                        #remove empty spaces
   			            while len(last_name)>0 and last_name[-1]==" ":
   			                last_name=last_name[:-1]
   			            first_name=out_df["Rider"].values[ii][len(last_name)+1:]
                               
   			            out_df["Rider"].values[ii]=first_name+" "+last_name
   			        else:
   			            print("no span found in: " +str(series[ii]))
   
   			out_df[col + '_ID'] = series.apply(lambda td: rider_link_to_id(td.a))
   			try:
   				out_df[col + '_Country'] = series.apply(lambda td: img_to_country_code(td.img))
   			except TypeError:
   				pass
   
   		elif col == 'Team':
   			out_df['Team_ID'] = series.apply(lambda td: team_link_to_id(td.a) if td.a else None)
   			out_df['Team_Country'] = series.apply(lambda td: img_to_country_code(td.img) if td.img else None)
   
   		elif col == 'Race':
   			out_df['Race_ID'] = series.apply(lambda td: get_url_parameters(td.a['href'])['r'] if td.a else None)
   			
   		elif col == 'Race_Country':
   			out_df['Race_Country'] = series.apply(lambda td: img_to_country_code(td.img) if td.img else None)
   
   		elif col == '':
   			try:
   				out_df['Icon'] = series.apply(lambda td: get_img_name(td.img) if td.img else None)
   			except AttributeError:
   				pass
   

   	out_df = out_df.replace({'-': None}).dropna(how='all', axis=1)
   	# TODO Remove Unnamed columns
   	
   	return out_df


