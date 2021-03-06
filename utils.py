import pandas as pd 
from pathlib import Path
import numpy as np
from sqlalchemy import create_engine
from urllib.parse import urlparse
import psycopg2
import math


def get_c(e, m):
    '''
    Calculates coefficient of variation, a
    measure of sampling error.
    
    Parameters
    ----------
    e: float
       Estimate value for variable of interest
    m: float
       MOE for variable of interest

    Returns
    -------
    float
        Coefficient of variation

    '''
    if e == 0:
        return np.nan
    else:
        return m/1.645/e*100

def get_p(e, agg_e):
    '''
    Calculates proportion/percent estimate.
    Returns None of the universe estimate is zero.
    
    Parameters
    ----------
    e: float
       Estimate value for numerator
    agg_e: float
       Estimate value of the universe variable, or
       proportion demoninator

    Returns
    -------
    float
        Estimate of proportion.
          
    '''
    if agg_e == 0:
        return np.nan
    else:
        return e/agg_e*100

def get_z(e, m, p, agg_e, agg_m):
    '''
    Calculates the standard error of proportion and 
    percent variables.
    
    Parameters
    ----------
    e: float
       Estimate value of the proportion numerator
    m: float
        MOE value of the numerator
    agg_e: float
       Estimate value of the universe variable, or
       proportion demoninator
    agg_m: float
       MOE value of the universe variable, or
       proportion demoninator

    Returns
    -------
    float
        Standard error of the percent variable

    '''
    if p == 0:
        return np.nan
    elif p == 100:
        return  np.nan
    elif agg_e == 0:
        return  np.nan
    elif m**2 - (e*agg_m/agg_e)**2 <0:
        return math.sqrt(m**2 + (e*agg_m/agg_e)**2)/agg_e*100
    else: 
        return math.sqrt(m**2 - (e*agg_m/agg_e)**2)/agg_e*100

def format_geoid(geoid):
    '''
    Parses the ACS GeoID field, converting county FIPS code to
    borough abbreviation.
    
    Parameters
    ----------
    geoid: str
        GEOID as found in downloaded ACS tables.

    Returns
    -------
    str
        Formatted ID, of the form BX + <smaller geography ID>

    '''
    fips_lookup = {
        '05': '2',
        '47': '3',
        '61': '1',
        '81': '4',
        '85': '5',}
    # NTA
    if geoid[:2] in ['MN', 'QN', 'BX', 'BK', 'SI']: 
        return geoid
    # Community District (PUMA)
    elif geoid[:2] == '79': 
        return geoid[-4:]
    # Census tract (CT2010)
    elif geoid[:2] == '14':
        boro = fips_lookup.get(geoid[-8:-6])
        return boro + geoid[-6:]
    # Boro
    elif geoid[:2] == '05': 
        return fips_lookup.get(geoid[-2:])
    # City 
    elif geoid[:2] == '16':
        return 0

def assign_geotype(geoid):
    '''
    Parses the ACS GeoID field to determine 
    what type of spatial unit a record refers to.
    
    Parameters
    ----------
    geoid: str
        GEOID as found in downloaded ACS tables.

    Returns
    -------
    str
        'NTA2010','PUMA2010','CT2010','Boro2010', or 'City2010'
        Type of geography

    ''' 
    # NTA
    if geoid[:2] in ['MN', 'QN', 'BX', 'BK', 'SI']: 
        return 'NTA2010'
    # Community District (PUMA)
    elif geoid[:2] == '79': 
        return 'PUMA2010'
    # Census tract (CT2010)
    elif geoid[:2] == '14':
        return 'CT2010'
    # Boro
    elif geoid[:2] == '05': 
        return 'Boro2010'
    # City 
    elif geoid[:2] == '16':
        return 'City2010'

def assign_geogname(geotype, name, geoid):
    '''
    Uses formatted GEOID to set appropriate name.
    These are full borough names, PUMA names, or NTA names.
    
    Parameters
    ----------
    geoid: str
        Formatted ID, of the form BX + <smaller geography ID>
        
    '''
    boro_lookup = {
        '1': 'Manhattan',
        '2': 'Bronx', 
        '3': 'Brooklyn',
        '4': 'Queens', 
        '5': 'Staten Island'}
    if geotype == 'Boro2010': 
        return boro_lookup.get(geoid)
    elif geotype == 'City2010': 
        return 'New York City'
    elif geotype == 'CT2010': 
        return NTA.nta_code[NTA.boroct == geoid].to_list()[0]
    elif geotype == 'PUMA2010': 
        return name
    elif geotype == 'NTA2010': 
        return NTA.nta_name[NTA.nta_code == geoid].to_list()[0]

NTA = pd.read_excel(Path(__file__).parent/'data/nyc2010census_tabulation_equiv.xlsx', 
                   skiprows=4, dtype=str,
                  names=['borough', 'fips', 'borough_code', 'tract', 'puma', 'nta_code', 'nta_name'])
NTA['boroct']=NTA['borough_code'] + NTA['tract']   

def psycopg2_connect(url):
    result = urlparse(str(url))
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    connection = psycopg2.connect(
        database = database,
        user = username,
        password = password,
        host = hostname, 
        port = port)
    return connection