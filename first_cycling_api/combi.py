#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 14 15:39:13 2023

@author: maxime
"""
from .race.race import RaceEdition

def combi_results_startlist(
        race_id: int, 
        year: int,
        classification_num=None, 
        stage_num=None,
        ):
	"""
    Combine the result and the start list
    
    Important to understand: basis is the result table as it is easy to interpret (one line = one rider with team included)
    The startlist is added afterwards, as it more difficult to interpret (riders listed below a team name)
    
	Attributes
	----------
	race_id: int
		 FC id of the race
    year: int   
	classification_num : int
		Classification for which to collect information.
		See utilities.Classifications for possible inputs.
	stage_num : int
		Stage number for which to collect results, if applicable.
		Input 0 for prologue.
	"""
	try:
	    r=RaceEdition(race_id=race_id,year=year)
	    t=r.results(classification_num=classification_num,stage_num=stage_num)

	    if stage_num is None and classification_num is None: #fallback only for startlist
	        if (t is None or (("results_table" in t.__dir__()) and 
                           (t.results_table is None or not str(t.results_table.iloc[0]["Pos"]).isnumeric()) #DNF as first, means the race is not finished
               )): 
	            print("fallback 1")
                #case of race not completed yet
	            r=RaceEdition(race_id=race_id,year=year)
	            t=r.results(classification_num=classification_num,stage_num=1)
	        if (t is None or (("results_table" in t.__dir__()) and 
                           (t.results_table is None or not "Inv name" in t.results_table.columns 
                            or not str(t.results_table.iloc[0]["Pos"]).isnumeric()))):    
                #fallback TTT as first stage
	            print("fallback 2")            
	            t=r.results(classification_num=classification_num,stage_num=2)

	    if "results_table" in t.__dir__() and t.results_table is not None:
	        results_table=t.results_table
	        start_list=r.startlist()
            
	        """ Convert HTML table from bs4 to pandas DataFrame. Return None if no data. """
	        # TODO for rider results, format dates nicely with hidden column we are throwing away
    
	        if "Inv name" in results_table.columns:
	            for i in results_table.index:
	                try:
	                    results_table.loc[i,"BIB"]=start_list.bib_df.loc[results_table.loc[i,"Inv name"]]["BIB"]
	                except:
	                    print(results_table.loc[i,"Inv name"] + " not found in the start list")
	                    results_table.loc[i,"BIB"]=0
	            t.results_table=results_table
	        else:
	            print("No Inv name in results_table, the stage may be a TTT")
	            return None
    
	        return t
	except Exception as msg:
	    import sys
	    _, _, exc_tb = sys.exc_info()
	    print("combi failed line " + str(exc_tb.tb_lineno))
	    print("classification num: " +str(classification_num))
	    print(msg)
        


