import os
import csv
import logging
import sys
import xml.etree.ElementTree as ET
import pandas as pd
logging.basicConfig(filename='myProgramLog.txt', filemode='w', level=logging.DEBUG, format=' %(asctime)s - %(levelname)s- %(message)s')

#gets a valid KML file from the user, quitting if they choose
def get_input_file():
    validFile = False
    directory=''
    while(not validFile):
        directory = input('Please enter a KML file to scan for coordinates (press q to quit): ')
        if(directory.lower().strip() == "q"):
            logging.debug('Quitting due to user input...')
            sys.exit()
        logging.debug(f'Validating path %s', directory)
        directoryStrLength = len(directory)
        if(os.path.isfile(directory)):
            if(directory[directoryStrLength-4:directoryStrLength] == '.kml'):
                validFile = True
            else:
                basename = os.path.basename(directory)
                logging.warning('User tried using this file: %s. Prompting Again.', basename)
                print(f'{basename} is not a .xml file. Try Again.')
        else:
            logging.warning('User gave an invalid file path: %s. Prompting Again.', directory)
            print('Invalid file path. Try Again.')
    return directory

def get_geometry_type(placemark, ns):
    if placemark.find('.//kml:Point', ns) is not None:
        return 'Point'
    elif placemark.find('.//kml:LineString', ns) is not None:
        return 'LineString'
    elif placemark.find('.//kml:Polygon', ns) is not None:
        return 'Polygon'
    else:
        return 'Other'

#--------------------------------Start of main program----------------------------------
#take data from KML file (like KML coordinate summarizer) and use pandas to summarize the coordinates

logging.info('Start of Program')

directory = get_input_file()

TXTName = input('Please enter the name of the TXT summary to be generated: ')

tree = ET.parse(directory)

dataframeList = [] #list to hold coordinate information


#define kml namespace
ns = {'kml': 'http://www.opengis.net/kml/2.2'}

logging.info('Gathering information from KML file...')

for placemark in tree.findall('.//kml:Placemark', ns):
    name = placemark.find('kml:name', ns)
    if name is not None:
        logging.debug(f'Processing Placemark: {name.text}')
        name = name.text
    else:
        logging.debug('Processing unnamed Placemark')
        name = 'Unnamed Placemark'

    geometryType = get_geometry_type(placemark, ns)
    logging.debug(f'Geometry type for Placemark {name}: {geometryType}')
    
    logging.debug(f'Finding coordinates for Placemark: {name}')
    for coord in placemark.findall('.//kml:coordinates', ns):
        coordText = coord.text
        coordList = coordText.split()
        for coordSet in coordList:
            coords = coordSet.split(',')
            logging.debug(f'Processing coordinates: {coords} for Placemark: {name}')
            longitude = float(coords[0])
            latitude = float(coords[1])
            altitude = float(coords[2])
            dataframeList.append({
                'Placemark Name': name,
                'Geometry Type': geometryType,
                'Longitude': longitude,
                'Latitude': latitude,
                'Altitude': altitude
            })

logging.info('Finished gathering information from KML file. Creating DataFrame...')
#create dataframe from list of dictionaries
df = pd.DataFrame(dataframeList)
logging.debug(f'Dataframe created: \n{df}\n')

logging.info('Dataframe created. Summarizing information...')
#getting information for the summary
#creates a sub dataframe grouping each name and their corresponding counts
placemarkCounts = df.groupby("Placemark Name").size().reset_index(name="Count")
boundingBox = {
    "min_lon": df["Longitude"].min(),
    "max_lon": df["Longitude"].max(),
    "min_lat": df["Latitude"].min(),
    "max_lat": df["Latitude"].max()
}
#summary of altitude information per placemark
altitudeSummary = df.groupby("Placemark Name")["Altitude"].agg(["min", "max", "mean"])
geometryTypes = df.groupby("Geometry Type").size().reset_index(name="Count")

logging.info('Summary information created. Writing to TXT file...')

with open(f'{TXTName}.txt', 'w') as file:
    file.write(f'---------------{os.path.basename(directory)} Summary---------------\n\n')
    file.write(f'Total Placemarks: {len(df)}\n\n')
    file.write(f'{placemarkCounts.to_string(index=False)}\n\n')
    file.write(f'Minimum Longitude: {boundingBox["min_lon"]}\n')
    file.write(f'Maximum Longitude: {boundingBox["max_lon"]}\n')
    file.write(f'Minimum Latitude: {boundingBox["min_lat"]}\n')
    file.write(f'Maximum Latitude: {boundingBox["max_lat"]}\n')
    file.write(f'\nAltitude Summary per Placemark:\n{altitudeSummary.to_string()}\n')
    file.write(f'\nGeometry Type Counts:\n{geometryTypes.to_string(index=False)}\n')

logging.info(f'TXT file {TXTName}.txt written successfully')