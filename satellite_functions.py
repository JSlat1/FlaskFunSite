from flask import Flask
from flask import request, escape, render_template, redirect, url_for, abort, jsonify, Blueprint

import urllib.request
import os
import json
from satellite_czml import satellite_czml
from satellite_czml import satellite
import random
from datetime import datetime, timedelta
import json
import czml
import pandas as pd
import numpy as np
import functools
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth

# Get current working directory
path = os.getcwd()

credential = ServiceAccountCredentials.from_json_keyfile_name("credentials.json",
    ["https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(credential)

########################################################################################
#Derive the id from the google drive shareable link.
#For the file at hand the link is as below
#df = pd.read_pickle(path)
#df = pd.read_csv(path)
#df.head()
########################################################################################

# Set Cesium API Key
cesiumApiKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIwMGZkMzlkYy0xNDdkLTQ5MTEtYjY2OS1jN2JjNzllNmZlMzgiLCJpZCI6ODc1MDMsImlhdCI6MTY0ODU3NjczMX0.1JhoIllSRmkhIjzTipN2UYWWSvTOC6eRx2T0sMzE3b0'


def requestTLEData():
  """Retrieves TLE Data from Celestrak"""
  #url = 'https://celestrak.com/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
  #result = urllib.request.urlopen(url)
  URL = 'https://drive.google.com/file/d/1m0mAGzpeMR0W-BDL5BtKrs0HOZsPIAbX/view?usp=sharing'
  drivePath = 'https://drive.google.com/uc?export=download&id='+URL.split('/')[-2]
  result = urllib.request.urlopen(drivePath)
  with open(path + '/tle data.txt', 'w') as tleDataFile:
    for line in result.readlines():
      tleDataFile.write(f"{str(line.decode('utf-8').strip())}\n")
    tleDataFile.close()

def createTleList():
  requestTLEData()
  # get tle data text file
  with open(path + "/tle data.txt", "r") as tledatafile:
      lineList = tledatafile.readlines()
  tledatafile.close()

  # iterate through list to group each set of tle data
  iter = 0
  storedSet = []

  for line in lineList:
      line = line.encode('utf-8').strip()
      line = line.decode('utf-8')
      storedSet.append(line)
      iter += 1
      if (iter > 2):
          tleDataList.append(storedSet)
          storedSet = []
          iter = 0

  # clean tle data sets
  for set in tleDataList:
      if str(set[0]).lower().strip() == 'lemur-2-dunlop':
          tleDataList.remove(set)

def fixTime(givenTime):
  """Fixes ISO 8601 DateTime"""
  fixed = str(givenTime).replace('/', '+00:00/')
  fixed = f"{fixed}+00:00"
  fixed = str(fixed).replace('t', 'T')
  return fixed

def fixCapitalization(givenDict):
  """Fixes final output capitalization to what Cesium recognizes"""
  wordReplaceList = ['horizontalOrigin', 'LEFT', 'outlineWidth',
                      'fillColor', 'solidColor', 'pixelSize',
                      'pixelOffset', 'currentTime', 'interpolationAlgorithm',
                      'interpolationDegree', 'referenceFrame', 'LAGRANGE',
                      'INERTIAL', 'Lucida Console', 'true',
                      'trailTime', 'leadTime', 'outlineColor']
  czmlDict = givenDict
  fixedStr = ""
  for word in wordReplaceList:
    fixedStr = str(json.dumps(czmlDict).replace(word.lower(), word))
    czmlDict = json.loads(fixedStr)
  return fixedStr

def fixCzmlFormat(givenCzml):
  """"Main Function for fixing CZML formatting"""
  json_dict = json.loads(givenCzml)
  i = 0
  for item in json_dict:
    for key in json_dict[i]:
      if (key == "clock"):
        json_dict[i][key]['currenttime'] = fixTime(json_dict[i][key]['currenttime'])
        json_dict[i][key]['interval'] = fixTime(json_dict[i][key]['interval'])
      if (key == 'availability'):
        json_dict[i][key] = fixTime(json_dict[i][key])
      if (key == 'position'):
        json_dict[i][key]['epoch'] = fixTime(json_dict[i][key]['epoch'])
      if (key == 'label'):
        json_dict[i][key]['show'] = True
      if (key == 'point'):
        json_dict[i][key]['show'] = True
      if (key == 'path'):
        json_dict[i][key]['show'][0]['interval'] = fixTime(json_dict[i][key]['show'][0]['interval'])
        json_dict[i][key]['show'][0]['boolean'] = True

        k = 0
        for leadtime in json_dict[i][key]['leadtime']:
          json_dict[i][key]['leadtime'][k] = {'interval':f"{fixTime(leadtime['interval'])}",
                                                      'epoch':f"{fixTime(leadtime['epoch'])}",
                                                      'number':leadtime['number']}
          k += 1

        k = 0
        for trailtime in json_dict[i][key]['trailtime']:
          json_dict[i][key]['trailtime'][k] = {'interval':f"{fixTime(trailtime['interval'])}",
                                                      'epoch':f"{fixTime(trailtime['epoch'])}",
                                                      'number':trailtime['number']}
          k += 1

    i += 1

  fixedTime = fixCapitalization(json_dict)

  return fixedTime

def buildCzml(givenTleList):
  satelliteList = []
  added_sat_ids = []
  remove_these_ids = []
  print(f"GivenTleList: {givenTleList}")
  for tle in givenTleList:
    if (str(tle[0]).strip() != 'LEMUR-2-DUNLOP'):
      sat = satellite(tle,
                      description = 'Satellite: ' + tle[0],
                      color = [random.randrange(256) for x in range(3)],
                      marker_scale = 12,
                      use_default_image = False,
                      start_time = datetime.strptime('2022-04-04 01:00:00', '%Y-%m-%d %H:%M:%S'),
                      end_time = datetime.strptime('2022-04-04 23:00:00', '%Y-%m-%d %H:%M:%S'),
                      show_label = True,
                      show_path = True)
      satelliteList.append(sat)
      added_sat_ids.append(sat.id)
  czml_obj = satellite_czml(satellite_list = satelliteList,
                            ignore_bad_tles = True,
                            speed_multiplier = 30)

  for satkey in czml_obj.satellites:
    if satkey not in added_sat_ids:
      remove_these_ids.append(satkey)

  for satkey in remove_these_ids:
    czml_obj.remove_satellite(satkey)

  czmlString = czml_obj.get_czml().lower()
  print(f"CzmlString: {czmlString}")
  czmlString = fixCzmlFormat(czmlString)
  with open(path + "/satellites.czml", "w") as satelliteFile:
    satelliteFile.write(czmlString)
    satelliteFile.close()
  return czmlString

def combineWithTLEs(tleList):
  tleList = list(tleList)
  satcatIds = []
  global tle_id_dict
  tle_id_dict = {}

  for tleItem in tleList:
    thisId = tleItem[2].split(' ')[1]
    satcatIds.append(thisId)
    tle_id_dict[thisId] = tleItem

  indexMask = df_final['Satcat'].isin(satcatIds)
  indexes = df_final.loc[indexMask, :].index
  df_final.insert(len(df_final.columns), 'TLE_0', np.nan, True)
  df_final.insert(len(df_final.columns), 'TLE_1', np.nan, True)
  df_final.insert(len(df_final.columns), 'TLE_2', np.nan, True)

  for indexVal in indexes:
    df_final.loc[indexVal, 'TLE_0'] = tle_id_dict[df_final.loc[indexVal, 'Satcat']][0]
    df_final.loc[indexVal, 'TLE_1'] = tle_id_dict[df_final.loc[indexVal, 'Satcat']][1]
    df_final.loc[indexVal, 'TLE_2'] = tle_id_dict[df_final.loc[indexVal, 'Satcat']][2]

  df_final.dropna(axis=0, how='any', subset=['TLE_0', 'TLE_1', 'TLE_2'], inplace=True)

def index(selectionInfo):
  shownCzml = ''
  inputList = []
  tlesToCzml = []
  updateViewer = False
  print(selectionInfo)
  try:
    selectionInfo = json.loads(selectionInfo)
    print(selectionInfo)
  except:
    print("Failed JSON Conversion")
    selectionInfo = ''
  if len(selectionInfo) > 0:
    for val in selectionInfo:
      inputList.append(val)
      print(val)
  if len(inputList) > 0:
    updateViewer = True
    tlesToCzml = []
    for selection in inputList:
      tlesToCzml.append(tle_id_dict[selection])
    shownCzml = json.loads(buildCzml(tlesToCzml))
  else:
    updateViewer=False
    inputList=[]

  return render_template('index.html', df_final=df_final, updateViewer=str(updateViewer), shownCzml=shownCzml)

tleDataList = []

fileNameList = ['currentcat', 'satcat', 'deepcat', 'deepindex', 'auxcat']

global currentFrame
global satcatFrame
global deepcatFrame
global deepIndexFrame
global auxcatFrame

fileIndex = 0

'''
for fileName in fileNameList:
  with open(path + "/EoC-Final-Project/CSVs/" + fileName + '.csv', 'r') as csvFile:
    if (fileName == 'currentcat'):
      currentFrame = pd.read_csv(csvFile, dtype=str)
    if (fileName == 'satcat'):
      satcatFrame = pd.read_csv(csvFile, dtype=str)
    if (fileName == 'deepcat'):
      deepcatFrame = pd.read_csv(csvFile, dtype=str)
    if (fileName == 'deepindex'):
      deepIndexFrame = pd.read_csv(csvFile, dtype=str)
    if (fileName == 'auxcat'):
      auxcatFrame = pd.read_csv(csvFile, dtype=str)
    csvFile.close()
'''

auxSheet = client.open("Test").worksheet("Auxcat")
satSheet = client.open("Test").worksheet("Satcat")
currSheet = client.open("Test").worksheet("Currentcat")
deepSheet = client.open("Test").worksheet("Deepcat")
deepIndSheet = client.open("Test").worksheet("DeepIndex")

satVals = satSheet.get_all_values()
currVals = currSheet.get_all_values()
deepVals = deepSheet.get_all_values()
deepIndVals = deepIndSheet.get_all_values()
auxVals = auxSheet.get_all_values()

satcatFrame = pd.DataFrame(data=satVals[1:len(satVals)-1], columns = satVals[0])
currentFrame = pd.DataFrame(data=currVals[1:len(currVals)-1], columns = currVals[0])
deepcatFrame = pd.DataFrame(data=deepVals[1:len(deepVals)-1], columns = deepVals[0])
deepIndexFrame = pd.DataFrame(data=deepIndVals[1:len(deepIndVals)-1], columns = deepIndVals[0])
auxcatFrame = pd.DataFrame(data=auxVals[1:len(auxVals)-1], columns = auxVals[0])

# find active objects
activeMask = currentFrame['Active'].str.find('A') != -1
activeFrame = currentFrame.loc[activeMask, :]

# create list of columns in active frame
activeFrameColumns = list(activeFrame.columns)
print(activeFrameColumns)

# Fix NaN values from NNA/NNA A/NNA C to pd.nan (AKA Pandas null value)
fixMask = activeFrame['Satcat'].str.find('NNA') != -1
#if len(fixMask.index > 0):
for satIndex in activeFrame.loc[fixMask, ['Satcat']].index:
    activeFrame.loc[satIndex, 'Satcat'] = np.nan

deepMask = activeFrame['DeepCat'].notna()
currentDeepDf = activeFrame.loc[deepMask, :]

# create list of columns for satcat and auxcat
satcatColumns = list(satcatFrame.columns)
auxcatColumns = list(auxcatFrame.columns)

# create merged list of columns
fullFrameColumns = []
fullFrameColumns.extend(activeFrameColumns)
fullFrameColumns.extend(satcatColumns)
fullFrameColumns.extend(auxcatColumns)

# remove duplicates from list and create
# list of columns added to activeFrame
# from satcat/auxcat dataframes
col_list = []
dif_col_list = []
for col in fullFrameColumns:
  if col not in col_list:
    col_list.append(col)
    if col not in activeFrameColumns:
        dif_col_list.append(col)
fullFrameColumns = col_list

# print column lists
print(fullFrameColumns)
print(dif_col_list)

# add JCAT to dif_col_list
dif_col_list.append('JCAT')

print(satcatFrame.head())
print(auxcatFrame.head())
print(satcatFrame.head())
#satAuxFrame = pd.concat([auxcatFrame, satcatFrame], axis=0)
satAuxFrame = pd.merge(satcatFrame, auxcatFrame, how='outer')

# merge activeFrame with satcatFrame
global df_final
df_final = pd.merge(activeFrame, satAuxFrame[dif_col_list], how='left', on='JCAT', suffixes=["", "_duplicate"])

# Create TLE Data List
createTleList()

# Combine this TLE data with
# detailed dataframe
combineWithTLEs(tleDataList)

# show final dataframe
print(df_final.columns)

'''
satSite = Blueprint("satellites", __name__, static_folder = "static", template_folder = "tempaltes")

@satSite.route("/satellites", methods=['GET'], defaults={'selectionInfo':''})
@satSite.route("/", methods=['GET'])
def satellites(selectionInfo):
  shownCzml = ''
  inputList = []
  tlesToCzml = []
  updateViewer = False
  print(selectionInfo)
  try:
    selectionInfo = json.loads(selectionInfo)
    print(selectionInfo)
  except:
    print("Failed JSON Conversion")
    selectionInfo = ''
  if len(selectionInfo) > 0:
    for val in selectionInfo:
      inputList.append(val)
      print(val)
  if len(inputList) > 0:
    updateViewer = True
    tlesToCzml = []
    for selection in inputList:
      tlesToCzml.append(tle_id_dict[selection])
    shownCzml = json.loads(buildCzml(tlesToCzml))
  else:
    updateViewer=False
    inputList=[]

  return render_template('sat_index.html', df_final=df_final, updateViewer=str(updateViewer), shownCzml=shownCzml)
'''